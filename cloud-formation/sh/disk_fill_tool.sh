#!/bin/bash

# (c) 2025 Amazon Web Services, Inc. All Rights Reserved.
# This AWS content is subject to the terms of C2E Task Order 5502/HM047623F0080

usage() {
  echo "Usage:"
  echo "  $0 [TARGET_USAGE] [MOUNT_PATH] [FILL_SIZE_MB]"
  echo "     Fill disk to TARGET_USAGE% (default: 85%) using files of FILL_SIZE_MB (default: 100MB)"
  echo ""
  echo "  $0 --clear [MOUNT_PATH]"
  echo "     Remove fillfile_* from MOUNT_PATH"
  echo ""
  echo "  $0 --help | -h"
  echo "     Show this help message"
  exit 1
}

# Show help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  usage
fi

# Clear mode
if [[ "$1" == "--clear" ]]; then
  MOUNT_PATH=${2:-/mnt/vol1}
  echo " Clearing fill files from $MOUNT_PATH..."
  find "$MOUNT_PATH" -type f -name 'fillfile_*' -delete
  echo " Fill files removed."
  exit 0
fi

TARGET_USAGE=${1:-85}
MOUNT_PATH=${2:-/mnt/vol1}
FILL_SIZE_MB=${3:-100}

# Get the device for the mount path
DEVICE=$(df "$MOUNT_PATH" | awk 'NR==2 {print $1}' | xargs basename)
DEVICE_ROOT=$(echo "$DEVICE" | sed 's/p[0-9]\+$//')

# Get token for IMDSv2
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60")

# Get region and instance ID
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

# Find EBS Volume ID using nvme list
VOLUME_ID=$(sudo nvme list | awk -v dev="/dev/$DEVICE_ROOT" '$1 == dev { gsub(/^vol/, "vol-", $3); print $3 }')

if [[ -z "$VOLUME_ID" ]]; then
  echo " Could not determine EBS volume ID."
  TOTAL_SIZE_MB=0
else
  TOTAL_SIZE_GB=$(aws ec2 describe-volumes --region "$REGION" \
    --volume-ids "$VOLUME_ID" \
    --query "Volumes[0].Size" --output text)
  TOTAL_SIZE_MB=$(( TOTAL_SIZE_GB * 1024 ))
fi

# Current Available space
AVAILABLE_MB=$(df -m "$MOUNT_PATH" | awk 'NR==2 {print $4}')
TARGET_USED_MB=$(( TOTAL_SIZE_MB * TARGET_USAGE / 100 ))
TARGET_FREE_MB=$(( TOTAL_SIZE_MB - TARGET_USED_MB ))
MAX_FILL_MB=$(( AVAILABLE_MB - TARGET_FREE_MB ))

echo ""
echo " Disk Pre-Fill Summary"
echo "     Mount Path: $MOUNT_PATH"
echo "     Volume ID: $VOLUME_ID"
echo "     Total Size: ${TOTAL_SIZE_MB}MB"
echo "     Target Usage: ${TARGET_USAGE}%"
echo "     Target Used: ${TARGET_USED_MB}MB"
echo "     Target Free: ${TARGET_FREE_MB}MB"
echo "     Current Available: ${AVAILABLE_MB}MB"
echo "     Max Fill Allowed: ${MAX_FILL_MB}MB"
echo ""

echo " Filling $MOUNT_PATH until usage reaches $TARGET_USAGE% using up to $FILL_SIZE_MB MB files..."

while true; do
  CURRENT_USAGE=$(df -h "$MOUNT_PATH" | awk 'NR==2 {gsub("%", "", $5); print $5}')
  CURRENT_AVAILABLE_MB=$(df -m "$MOUNT_PATH" | awk 'NR==2 {print $4}')
  echo " Usage: ${CURRENT_USAGE}%, Available: ${CURRENT_AVAILABLE_MB}MB"

  if [ "$CURRENT_USAGE" -ge "$TARGET_USAGE" ]; then
    echo " Target reached."
    break
  fi

  CURRENT_USED_MB=$(( TOTAL_SIZE_MB - CURRENT_AVAILABLE_MB ))
  NEEDED_MB=$(( TARGET_USED_MB - CURRENT_USED_MB ))

  if (( NEEDED_MB <= 0 )); then
    echo " No space needed to reach target."
    break
  fi

  WRITE_MB=$(( FILL_SIZE_MB < NEEDED_MB ? FILL_SIZE_MB : NEEDED_MB ))
  FILL_FILE="$MOUNT_PATH/fillfile_$(date +%s)"
  echo "  Writing ${WRITE_MB}MB to $FILL_FILE..."
  dd if=/dev/zero of="$FILL_FILE" bs=1M count="$WRITE_MB" status=none
done
