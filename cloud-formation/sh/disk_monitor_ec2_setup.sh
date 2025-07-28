#!/bin/bash

# (c) 2025 Amazon Web Services, Inc. All Rights Reserved.
# This AWS content is subject to the terms of C2E Task Order 5502/HM047623F0080

# Update system and install dependencies
yum update -y
yum install -y amazon-cloudwatch-agent nvme-cli

# Wait for attached volumes to appear
for device in /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1; do
  while [ ! -e "$device" ]; do
    echo "Waiting for $device to be attached..."
    sleep 3
  done
done

# Format the attached volumes with ext4 filesystem
mkfs.ext4 /dev/nvme1n1
mkfs.ext4 /dev/nvme2n1
mkfs.ext4 /dev/nvme3n1

# Create mount points
mkdir -p /mnt/vol1 /mnt/vol2 /mnt/vol3

# Get UUIDs and persist to /etc/fstab
UUID1=$(blkid -s UUID -o value /dev/nvme1n1)
UUID2=$(blkid -s UUID -o value /dev/nvme2n1)
UUID3=$(blkid -s UUID -o value /dev/nvme3n1)

echo "UUID=$UUID1 /mnt/vol1 ext4 defaults,nofail 0 2" >> /etc/fstab
echo "UUID=$UUID2 /mnt/vol2 ext4 defaults,nofail 0 2" >> /etc/fstab
echo "UUID=$UUID3 /mnt/vol3 ext4 defaults,nofail 0 2" >> /etc/fstab

# Mount all volumes
mount -a

# Create CloudWatch Agent config
tee /opt/aws/amazon-cloudwatch-agent/bin/config.json > /dev/null <<EOF
{
  "metrics": {
    "metrics_collected": {
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["/mnt/vol1", "/mnt/vol2", "/mnt/vol3"],
        "drop_device": true,
        "drop_mount": false,
        "drop_fstype": true
      }
    },
    "append_dimensions": {
      "InstanceId": "\${aws:InstanceId}"
    }
  }
}
EOF

# Start the CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json \
  -s

# Record output
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status > /tmp/agent_status.txt

