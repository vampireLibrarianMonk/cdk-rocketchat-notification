#!/bin/bash
# Script to generate a .env.cdk.params file from a template with preserved comments

#!/bin/bash
# Script to generate a .env.cdk.params file from a template with preserved comments

OUTPUT_FILE=".env.cdk.params"

# Check if the file already exists
if [ -f "$OUTPUT_FILE" ]; then
  read -p "$OUTPUT_FILE already exists. Overwrite? (y/n): " confirm
  case "$confirm" in
    [yY][eE][sS]|[yY]) 
      echo "Overwriting $OUTPUT_FILE..."
      ;;
    *)
      echo "Aborted. File not overwritten."
      exit 1
      ;;
  esac
fi

# Write content to the file
OUTPUT_FILE=.env.cdk.params
echo "# === Environment configuration for CDK deployments ===" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# Ensure the FACILITY_PREFIX_LIST_ID is found per company policy or is created/recorded prior." >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# Ensure the AVAILABILITY_ZONE coincides in the region where you will pick the FACILITY_PREFIX_LIST_ID." >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# For env_setup_stack.py" >> $OUTPUT_FILE
echo "AVAILABILITY_ZONE={VALUE}" >> $OUTPUT_FILE
echo "CIDR_DISK_MONITOR_VPC=10.10.0.0/28" >> $OUTPUT_FILE
echo "CIDR_ROCKETCHAT_VPC=10.20.0.0/28" >> $OUTPUT_FILE
echo "CIDR_LAMBDA_VPC=10.0.0.0/27" >> $OUTPUT_FILE
echo "FACILITY_PREFIX_LIST_ID={VALUE}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# For disk_monitor_stack.py" >> $OUTPUT_FILE
echo "DISK_MONITOR_SUBNET={VALUE}" >> $OUTPUT_FILE
echo "DISK_MONITOR_SG={VALUE}" >> $OUTPUT_FILE
echo "DISK_MONITOR_KEY_PAIR={VALUE}" >> $OUTPUT_FILE
echo "DISK_MONITOR_IMAGE_ID={VALUE}" >> $OUTPUT_FILE
echo "DISK_FILL_SCRIPT_S3={VALUE}" >> $OUTPUT_FILE
echo "DISK_FILL_SCRIPT_KEY={VALUE}" >> $OUTPUT_FILE
echo "DISK_MONITOR_SETUP_S3={VALUE}" >> $OUTPUT_FILE
echo "DISK_MONITOR_SETUP_KEY={VALUE}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# For the rocketchat_stack.py" >> $OUTPUT_FILE
echo "ROCKETCHAT_SUBNET={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_SG={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_EIP_ALLOC_ID={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_KEY_PAIR={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_IMAGE_ID={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_SETUP_SCRIPT_S3={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_SETUP_SCRIPT_KEY={VALUE}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# For the lambda_stack.py" >> $OUTPUT_FILE
echo "LAMBDA_VPC={VALUE}" >> $OUTPUT_FILE
echo "LAMBDA_SG={VALUE}" >> $OUTPUT_FILE
echo "LAMBDA_PRIVATE_SUBNET={VALUE}" >> $OUTPUT_FILE
echo "LAMBDA_PUBLIC_SUBNET={VALUE}" >> $OUTPUT_FILE
echo "LAMBDA_S3_BUCKET={VALUE}" >> $OUTPUT_FILE
echo "LAMBDA_S3_KEY={VALUE}" >> $OUTPUT_FILE
echo "DISK_THRESHOLD_PERCENT={VALUE}" >> $OUTPUT_FILE
echo "ROCKETCHAT_WEBHOOK_URL={VALUE}" >> $OUTPUT_FILE
echo "AVAILABILITY_ZONE={VALUE}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "# For the cloudwatch_alarm_stack.py" >> $OUTPUT_FILE
echo "DISK_MONITOR_INSTANCE_ID={VALUE}" >> $OUTPUT_FILE
echo "DISK_USAGE_ALERTS_TOPIC_ARN={VALUE}" >> $OUTPUT_FILE
echo "DISK_THRESHOLD_PARAM_NAME={VALUE}" >> $OUTPUT_FILE
