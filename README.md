## Environment Setup

This project uses the **AWS Cloud Development Kit (CDK)** with **Python** and requires **Node.js 20+**. The default Python version is expected to be `python3` as provided by Ubuntu (typically Python 3.10+).

---

### 1. Install Node.js 20 (Ubuntu)

Install Node.js 20 via the official NodeSource repo:

```bash
# Remove any older version (optional)
sudo apt remove -y nodejs
```

#### Add NodeSource for Node.js 20
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### Node and NPM version check
```bash
node -v   # should be v20.x.x
npm -v    # should be ≥8.x
```

### 2. Install AWS CDK CLI
Install the CDK command line globally:

```bash
sudo npm install -g aws-cdk
cdk --version
```

### 3. Set Up Python Virtual Environment

This project uses Python 3.10 or 3.11. Confirm that both Python and `pip` are available before creating the virtual environment.

#### Check Your Python & pip Versions

```bash
python3 --version     # should be 3.10 or 3.11
pip3 --version        # make sure pip is installed
```

#### If either is missing or not at the expected version, you may need to install or upgrade:

```bash
# Install Python 3.10 or 3.11 if needed
sudo apt update
sudo apt install -y python3.10 python3-pip
```

#### or for 3.11
```bash
sudo apt install -y python3.11 python3-pip
```

#### The following install will prevent the `ensurepip` error does not occur:
The virtual environment was not created successfully because ensurepip is not available.

```bash
# For Python 3.10
sudo apt install python3.10-venv

# Or for Python 3.11
sudo apt install python3.11-venv
```

#### Create and Activate the Virtual Environment
```bash
python3 -m venv .venv
```

#### Once created, activate the environment:
```bash
source .venv/bin/activate
```

### 4. Install core CDK Python dependencies:

```bash
pip install --upgrade pip
pip install aws-cdk-lib constructs
```

### 5. (Optional) Install any additional Python packages:

```bash
pip install -r requirements.txt
```

### 6. Initialize or Deploy CDK App
If this is your first time in the project directory:

```bash
cdk init app --language python  # only if cdk.json is missing
```

Then synthesize and deploy:

```bash
cdk synth
cdk deploy
```

# Notes:
The system python3 will be used by default (you can override manually with another version if desired).

Ensure .venv/bin/activate is sourced before installing any Python packages or running CDK commands.

Node.js 20 is required for CDK CLI v2.x to function properly.

## Cloud Development Kit (CDK)

### 1. How to Use
Source the environment file:

```bash
source .env.cdk.params
```

### 2. CDK Bootstrap (Required Once per Account/Region)
Before deploying any AWS CDK stack in a new account or region, you must bootstrap the environment. This process sets up essential resources that CDK needs to perform deployments—such as an S3 bucket for storing Lambda code and other assets, and IAM roles used by the CDK CLI.

What Bootstrapping Does
* Bootstrapping provisions the following in your AWS account:
* A deployment S3 bucket (e.g., cdk-hnb659fds-assets-<account>-<region>)
* IAM roles like cdk-hnb659fds-deploy-role

An SSM parameter /cdk-bootstrap/hnb659fds/version used to track bootstrap status

To Bootstrap Your Environment
Run the following command (replace region/account if needed):

```bash
cdk bootstrap aws://<account_id>/<region>
```

This only needs to be done once per AWS account and region combination. If your deployment fails with an error about missing /cdk-bootstrap/hnb659fds/version, this step has not been completed.

### 3. Key Pair Creation for EC2 Instance Access

Step 1: Create your key pair manually (e.g., ebs_alert_tester.pem and rocketchat_login.pem) via AWS Console or CLI:

```bash
aws ec2 create-key-pair --key-name rocketchat_login --query 'KeyMaterial' --output text > [rocketchat_login.pem|ebs_alert_tester]
chmod 400 [rocketchat_login.pem|ebs_alert_tester]
```

### 4. Retrieving the Rocket.Chat Elastic IP Allocation ID
The CDK stack creates and associates an Elastic IP (EIP) for the Rocket.Chat EC2 instance. However, due to AWS limitations, the EIP Allocation ID (e.g., eipalloc-xxxxxxxxxxxx) cannot be directly output in the CloudFormation Outputs when using the CfnEIP construct.

To retrieve it:
* Locate the output value named ROCKETCHATEIP (this is the public IP address).
* Use the following AWS CLI command to find the corresponding Allocation ID:

```bash
aws ec2 describe-addresses \
  --filters "Name=public-ip,Values=<ROCKETCHATEIP>" \
  --query "Addresses[0].AllocationId" \
  --output text
```

Replace <ROCKETCHATEIP> with the actual IP shown in the CDK output.

Once retrieved, set it as an environment variable `ROCKETCHAT_EIP_ALLOC_ID` in `.env.cdk.params`.

### 5. Packaging Lambda Function for CDK Deployment
To zip the Lambda function located at cloud-formation/lambda/code/lambda_function.py:

```bash
zip -j lambda_function.zip cloud-formation/lambda/code/lambda_function.py
```

Note: The -j flag strips directory paths so only the .py file is zipped at the root level, as required by AWS Lambda.

Upload the resulting lambda_function.zip to your designated S3 `LAMBDA_S3_BUCKET` and `LAMBDA_S3_KEY` in `.env.cdk.params` before CDK deployment.

### 6. Disk Monitor Script Upload
To support disk fill testing and EC2 setup, upload the following scripts to your designated S3 bucket locations:

| Script Source Path                            | Target S3 Bucket Key                        | .env.cdk.params Variables                              |
|----------------------------------------------|---------------------------------------------|-----------------------------------------------------|
| `cloud-formation/sh/disk_fill_tool.sh`       | `scripts/disk_fill_tool.sh`                | `DISK_FILL_SCRIPT_S3`, `DISK_FILL_SCRIPT_KEY`       |
| `cloud-formation/sh/disk_monitor_ec2_setup.sh`| `user-data/disk_monitor_ec2_setup.sh`      | `DISK_MONITOR_SETUP_S3`, `DISK_MONITOR_SETUP_KEY`   |

Use the appropriate bucket for each script as defined in your environment:
* DISK_FILL_SCRIPT_S3: bucket for the fill tool
* DISK_MONITOR_SETUP_S3: bucket for the EC2 setup script

These scripts are automatically fetched and executed as part of the EC2 instance's user data.

### 7. Rocket.Chat Setup Script Upload

Before deploying the Rocket.Chat stack, upload the setup script to the designated S3 bucket and key.

| Script Source Path                            | Target S3 Bucket Key                        | Related Env Variables                                     |
|----------------------------------------------|---------------------------------------------|------------------------------------------------------------|
| `cloud-formation/sh/rocketchat_setup.sh`     | `user-data/rocketchat_setup.sh`            | `ROCKETCHAT_SETUP_SCRIPT_S3`, `ROCKETCHAT_SETUP_SCRIPT_KEY` |

The EC2 instance will fetch and execute this script on boot using the User Data field.

### 8. Deploy CDK Stacks (using deploy.sh)
To simplify deployment and enforce proper stack order, use the included deploy.sh script located in the project root.

This script:
* Loads your environment parameters from .env.cdk.params
* Activates your virtual environment (if present)
* Deploys CDK stacks with the correct parameters
* Ensures EnvSetupStack is deployed before DiskMonitorStack and DiskMonitorStack before RocketChatStack

### 9. One-Time Setup
Important to note the following before using the `deploy.sh`
* Ensure the FACILITY_PREFIX_LIST_ID is found per company policy or is created/recorded prior.
* Ensure the AVAILABILITY_ZONE coincides in the region where you will pick the FACILITY_PREFIX_LIST_ID.

Ensure deploy.sh is executable:

```bash
chmod +x deploy.sh
```

### 10. Full Deployment (in proper order)
```bash
./deploy.sh all
```

This will:
* Deploy EnvSetupStack (VPCs, subnets, networking)
* Deploy DiskMonitorStack (EC2 instance, volumes, IAM)
* Deploy RocketChatStack (EC2 instance + EIP for Rocket.Chat)
* Deploy LambdaStack (Lambda function inside VPC, SSM-integrated, triggered via SNS)
* Deploy CloudWatchAlarmStack (Disk usage alarms on EC2 instance volumes, connected to Lambda via SNS)

### 11. Deploy Individual Stacks
⚠️ Ensure EnvSetupStack is deployed first. DiskMonitorStack, RocketChatStack, and LambdaStack all rely on subnet, security group or networking outputs created in that foundational stack. Additionally, CloudWatchAlarmStack depends on both EnvSetupStack and the EC2 instance provisioned by DiskMonitorStack.

Deploy Env Setup Stack

This foundational stack provisions the networking layer, including VPC, public and private subnets, route tables, internet gateway, NAT gateway and security groups. It provides shared infrastructure used by all other stacks.

```bash
./deploy.sh EnvSetupStack
```

Deploy Disk Monitor Stack
This stack provisions an EC2 instance with three attached EBS volumes mounted at /mnt/vol1, /mnt/vol2, and /mnt/vol3. It configures CloudWatch Agent and IAM permissions for metric collection and remote management.

```bash
./deploy.sh DiskMonitorStack
```

Deploy RocketChat Stack
This stack launches a self-hosted Rocket.Chat server on an EC2 instance, assigning it a static Elastic IP. It uses user data to automate the full startup and installation process.

```bash
./deploy.sh RocketChatStack
```

Deploy Lambda Notification Stack
This stack provisions a Lambda function that runs inside a private subnet with NAT access. It posts disk usage alerts to Rocket.Chat using a webhook stored in AWS SSM, and is triggered by an SNS topic subscribed to CloudWatch alarms.

```bash
./deploy.sh LambdaStack
```

Deploy CloudWatch Alarm Stack
This stack sets up CloudWatch alarms on /mnt/vol1, /mnt/vol2, and /mnt/vol3, using CloudWatch Agent metrics collected from the EC2 instance. The alarms are configured to trigger when disk usage exceeds a threshold pulled dynamically from AWS SSM.

```bash
./deploy.sh CloudWatchAlarmStack
```