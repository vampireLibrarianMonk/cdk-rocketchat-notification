#!/bin/bash

set -e

# Update and install Docker
dnf update -y
dnf install -y docker

# Enable and start Docker
systemctl enable --now docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create data directories
mkdir -p /home/ec2-user/rocketchat/data/db /home/ec2-user/rocketchat/data/dump
chown -R ec2-user:ec2-user /home/ec2-user/rocketchat

# Get the EC2 instance's private IP (IMDSv2-compatible)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

EC2_PRIVATE_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/local-ipv4)

# Start MongoDB container
docker run -d \
  --name mongo \
  --network host \
  -v /home/ec2-user/rocketchat/data/db:/data/db \
  -v /home/ec2-user/rocketchat/data/dump:/dump \
  mongo:5.0 \
  mongod --replSet rs0 --bind_ip_all

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to start..."
sleep 10

# Initialize MongoDB replica set
docker exec mongo mongosh --eval "rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: '${EC2_PRIVATE_IP}:27017' }
  ]
})"

# Wait briefly for replica set to become primary
sleep 5

# Start Rocket.Chat container
docker run -d \
  --name rocketchat \
  --network host \
  --env MONGO_URL="mongodb://${EC2_PRIVATE_IP}:27017/rocketchat?replicaSet=rs0" \
  --env ROOT_URL="http://${EC2_PRIVATE_IP}:3000" \
  --env PORT=3000 \
  --env MONGO_OPLOG_URL="mongodb://${EC2_PRIVATE_IP}:27017/local?replicaSet=rs0" \
  rocketchat/rocket.chat:latest

echo "Rocket.Chat setup complete and running at: http://${EC2_PRIVATE_IP}:3000"
