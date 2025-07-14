#!/bin/bash

set -euo pipefail

# Load environment variables
ENV_FILE=".env.cdk.params"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ $ENV_FILE not found in project root."
  exit 1
fi

source "$ENV_FILE"

# Activate .venv if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# === Helper function: deploy stack with parameters ===
deploy_env_stack() {
  : "${AVAILABILITY_ZONE:?Missing AVAILABILITY_ZONE}"
  : "${CIDR_DISK_MONITOR_VPC:?Missing CIDR_DISK_MONITOR_VPC}"
  : "${CIDR_ROCKETCHAT_VPC:?Missing CIDR_ROCKETCHAT_VPC}"
  : "${CIDR_LAMBDA_VPC:?Missing CIDR_LAMBDA_VPC}"
  : "${FACILITY_PREFIX_LIST_ID:?Missing FACILITY_PREFIX_LIST_ID}"

  echo "🌐 Deploying EnvSetupStack..."
  cdk deploy EnvSetupStack \
    --parameters AvailabilityZone=$AVAILABILITY_ZONE \
    --parameters CIDRDiskMonitorVPC=$CIDR_DISK_MONITOR_VPC \
    --parameters CIDRRocketChatVPC=$CIDR_ROCKETCHAT_VPC \
    --parameters CIDRLambdaVPC=$CIDR_LAMBDA_VPC \
    --parameters FacilityPrefixListId=$FACILITY_PREFIX_LIST_ID \
    "$@"
}

deploy_disk_stack() {
  : "${DISK_MONITOR_SUBNET:?Missing DISK_MONITOR_SUBNET}"
  : "${DISK_MONITOR_SG:?Missing DISK_MONITOR_SG}"
  : "${KEY_PAIR_NAME:?Missing KEY_PAIR_NAME}"
  : "${IMAGE_ID:?Missing IMAGE_ID}"

  echo "💽 Deploying DiskMonitorStack..."
  cdk deploy DiskMonitorStack \
    --parameters DiskMonitorSubnet=$DISK_MONITOR_SUBNET \
    --parameters DiskMonitorSG=$DISK_MONITOR_SG \
    --parameters KeyPairName=$KEY_PAIR_NAME \
    --parameters ImageId=$IMAGE_ID \
    "$@"
}

deploy_rocketchat_stack() {
  : "${ROCKETCHAT_SUBNET:?Missing ROCKETCHAT_SUBNET}"
  : "${ROCKETCHAT_SG:?Missing ROCKETCHAT_SG}"
  : "${ROCKETCHAT_EIP_ALLOC_ID:?Missing ROCKETCHAT_EIP_ALLOC_ID}"
  : "${ROCKETCHAT_KEY_PAIR:?Missing ROCKETCHAT_KEY_PAIR}"
  : "${ROCKETCHAT_IMAGE_ID:?Missing ROCKETCHAT_IMAGE_ID}"

  echo "💬 Deploying RocketChatStack..."
  cdk deploy RocketChatStack \
    --parameters RocketChatSubnet=$ROCKETCHAT_SUBNET \
    --parameters RocketChatSG=$ROCKETCHAT_SG \
    --parameters RocketChatEIPAllocationId=$ROCKETCHAT_EIP_ALLOC_ID \
    --parameters KeyPairName=$ROCKETCHAT_KEY_PAIR \
    --parameters ImageId=$ROCKETCHAT_IMAGE_ID \
    "$@"
}

deploy_lambda_stack() {
  : "${LAMBDA_VPC:?Missing LAMBDA_VPC}"
  : "${LAMBDA_SG:?Missing LAMBDA_SG}"
  : "${LAMBDA_PRIVATE_SUBNET:?Missing LAMBDA_PRIVATE_SUBNET}"
  : "${LAMBDA_S3_BUCKET:?Missing LAMBDA_S3_BUCKET}"
  : "${LAMBDA_S3_KEY:?Missing LAMBDA_S3_KEY}"
  : "${DISK_THRESHOLD_PERCENT:?Missing DISK_THRESHOLD_PERCENT}"
  : "${ROCKETCHAT_WEBHOOK_URL:?Missing ROCKETCHAT_WEBHOOK_URL}"

  echo "🛎️  Deploying LambdaStack..."
  cdk deploy LambdaStack \
    --parameters LambdaVPC=$LAMBDA_VPC \
    --parameters LambdaSG=$LAMBDA_SG \
    --parameters LambdaPrivateSubnet=$LAMBDA_PRIVATE_SUBNET \
    --parameters LambdaFunctionS3Bucket=$LAMBDA_S3_BUCKET \
    --parameters LambdaFunctionS3Key=$LAMBDA_S3_KEY \
    --parameters DiskThresholdPercent=$DISK_THRESHOLD_PERCENT \
    --parameters RocketChatWebhookURL=$ROCKETCHAT_WEBHOOK_URL \
    "$@"
}

deploy_cloudwatch_alarm_stack() {
  : "${DISK_MONITOR_INSTANCE_ID:?Missing DISK_MONITOR_INSTANCE_ID}"
  : "${DISK_USAGE_ALERTS_TOPIC_ARN:?Missing DISK_USAGE_ALERTS_TOPIC_ARN}"
  : "${DISK_THRESHOLD_PARAM_NAME:?Missing DISK_THRESHOLD_PARAM_NAME}"

  echo "📊 Deploying CloudWatchAlarmStack..."
  cdk deploy CloudWatchAlarmStack \
    --parameters InstanceId=$DISK_MONITOR_INSTANCE_ID \
    --parameters DiskUsageAlertsTopic=$DISK_USAGE_ALERTS_TOPIC_ARN \
    --parameters DiskThreshold=$DISK_THRESHOLD_PARAM_NAME \
    "$@"
}

# === Main dispatcher ===
if [ $# -eq 0 ]; then
  echo "Usage: ./deploy.sh [EnvSetupStack|DiskMonitorStack|RocketChatStack|LambdaStack|CloudWatchAlarmStack|all]"
  exit 1
fi

case "$1" in
  EnvSetupStack)
    deploy_env_stack "${@:2}"
    ;;
  DiskMonitorStack)
    deploy_disk_stack "${@:2}"
    ;;
  RocketChatStack)
    deploy_rocketchat_stack "${@:2}"
    ;;
  LambdaStack)
    deploy_lambda_stack "${@:2}"
    ;;
  CloudWatchAlarmStack)
    deploy_cloudwatch_alarm_stack "${@:2}"
    ;;
  all)
    deploy_env_stack
    deploy_disk_stack
    deploy_rocketchat_stack
    deploy_lambda_stack
    deploy_cloudwatch_alarm_stack
    ;;
  *)
    echo "❌ Unknown argument: $1"
    echo "Valid options: EnvSetupStack, DiskMonitorStack, RocketChatStack, LambdaStack, CloudWatchAlarmStack or all"
    exit 1
    ;;
esac
