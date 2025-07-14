#!/bin/bash

set -e

# Update and install Docker
dnf update -y
dnf install -y docker

# Enable and start Docker
systemctl enable --now docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create persistent data directories for MongoDB
echo "Creating data directories for MongoDB..."
mkdir -p /home/ec2-user/rocketchat/data/db /home/ec2-user/rocketchat/data/dump
chown -R ec2-user:ec2-user /home/ec2-user/rocketchat
echo "Data directories created and ownership assigned."

# Get the EC2 instance's private IP using IMDSv2
echo "Retrieving EC2 instance private IP from instance metadata..."
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

EC2_PRIVATE_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/local-ipv4)

echo "Private IP detected: $EC2_PRIVATE_IP"

# Start MongoDB container with replica set enabled
echo "Starting MongoDB container..."
docker run -d \
  --name mongo \
  --network host \
  -v /home/ec2-user/rocketchat/data/db:/data/db \
  -v /home/ec2-user/rocketchat/data/dump:/dump \
  mongo:5.0 \
  mongod --replSet rs0 --bind_ip_all

# Wait for MongoDB container to be ready
echo "Waiting for MongoDB to initialize..."
sleep 10

# Initialize the MongoDB replica set
echo "Initializing MongoDB replica set..."
docker exec mongo mongosh --eval "rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: '${EC2_PRIVATE_IP}:27017' }
  ]
})"

# Wait briefly for replica set election
echo "Waiting for replica set to stabilize..."
sleep 5

# Start Rocket.Chat container
echo "Starting Rocket.Chat container..."
docker run -d \
  --name rocketchat \
  --network host \
  -e MONGO_URL="mongodb://${EC2_PRIVATE_IP}:27017/rocketchat?replicaSet=rs0" \
  -e MONGO_OPLOG_URL="mongodb://${EC2_PRIVATE_IP}:27017/local?replicaSet=rs0" \
  -e ROOT_URL="http://${EC2_PRIVATE_IP}:3000" \
  -e ADMIN_USERNAME=ec2-user \
  -e ADMIN_PASS=StrongPassword123! \
  -e ADMIN_EMAIL=admin@example.com \
  -e OVERWRITE_SETTING_Show_Setup_Wizard=completed \
  rocketchat/rocket.chat:latest

# Wait for Rocket.Chat to become available
echo "Waiting for Rocket.Chat to be ready..."
for i in {1..30}; do
  sleep 5
  if curl -s "http://${EC2_PRIVATE_IP}:3000/api/info" | grep '"version"'; then
    echo "Rocket.Chat is ready."
    break
  else
    echo "Still waiting... ($i/30)"
  fi
done

echo "Rocket.Chat Docker setup complete and accessible at: http://${EC2_PRIVATE_IP}:3000"

echo "Starting Rocket.Chat administration setup on EC2 instance with private IP: ${EC2_PRIVATE_IP}"

echo "Authenticating admin user to get auth token..."
LOGIN_JSON=$(curl -s -H "Content-type: application/json" http://localhost:3000/api/v1/login -d '{
  "user": "ec2-user",
  "password": "StrongPassword123!"
}')

AUTH_TOKEN=$(echo "$LOGIN_JSON" | jq -r .data.authToken)
USER_ID=$(echo "$LOGIN_JSON" | jq -r .data.userId)
echo "Received auth token and user ID"

echo "Setting Rocket.Chat site URL to http://${EC2_PRIVATE_IP}:3000 ..."
curl -s -H "X-Auth-Token: $AUTH_TOKEN" \
     -H "X-User-Id: $USER_ID" \
     -H "Content-type: application/json" \
     http://localhost:3000/api/v1/settings/Site_Url \
     -d "{ \"value\": \"http://${EC2_PRIVATE_IP}:3000\" }"

echo "Creating #alerts channel..."
curl -s -H "X-Auth-Token: $AUTH_TOKEN" \
     -H "X-User-Id: $USER_ID" \
     -H "Content-type: application/json" \
     http://localhost:3000/api/v1/channels.create \
     -d '{ "name": "alerts" }'

echo "Creating incoming webhook integration for Disk Usage Alerts..."
CREATE_RESPONSE=$(curl -s -H "X-Auth-Token: $AUTH_TOKEN" \
     -H "X-User-Id: $USER_ID" \
     -H "Content-type: application/json" \
     http://localhost:3000/api/v1/integrations.create \
     -d "{
       \"type\": \"webhook-incoming\",
       \"name\": \"Disk Usage Alerts\",
       \"enabled\": true,
       \"username\": \"ec2-user\",
       \"channel\": \"#alerts\",
       \"scriptEnabled\": false
     }")

WEBHOOK_ID=$(echo "$CREATE_RESPONSE" | jq -r .integration._id)

echo "Setup complete. Rocket.Chat is running at http://${EC2_PRIVATE_IP}:3000"