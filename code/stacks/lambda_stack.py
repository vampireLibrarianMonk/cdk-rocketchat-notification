from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_s3 as s3,
    CfnParameter,
    CfnOutput,
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # === Parameters ===
        lambda_vpc = CfnParameter(self, "LambdaVPC", type="AWS::EC2::VPC::Id")
        lambda_sg = CfnParameter(self, "LambdaSG", type="AWS::EC2::SecurityGroup::Id")
        lambda_private_subnet = CfnParameter(self, "LambdaPrivateSubnet", type="AWS::EC2::Subnet::Id")
        lambda_public_subnet = CfnParameter(self, "LambdaPublicSubnet", type="AWS::EC2::Subnet::Id")
        lambda_bucket = CfnParameter(self, "LambdaS3Bucket", type="String")
        lambda_key = CfnParameter(self, "LambdaS3Key", type="String")
        disk_threshold = CfnParameter(self, "DiskThresholdPercent", type="String")
        webhook_url = CfnParameter(self, "RocketChatWebhookURL", type="String", no_echo=True)
        availability_zone = CfnParameter(self, "AvailabilityZone", type="String")

        # === SSM Parameters ===
        disk_threshold_param = ssm.StringParameter(self, "DiskUsageThresholdParameter",
            parameter_name="/diskmonitor/threshold/percent",
            string_value=disk_threshold.value_as_string,
            description="Threshold for disk usage alarm in percent (e.g. 85)"
        )

        webhook_param = ssm.StringParameter(self, "WebhookSSMParameter",
            parameter_name="/rocketchat/webhook_url",
            string_value=webhook_url.value_as_string,
            description="Webhook for Rocket.Chat alerts"
        )

        # === IAM Role ===
        lambda_role = iam.Role(self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )

        # === VPC Reference with Both Subnets ===
        vpc = ec2.Vpc.from_vpc_attributes(self, "LambdaVPCRef",
            vpc_id=lambda_vpc.value_as_string,
            availability_zones=[availability_zone.value_as_string],
            private_subnet_ids=[lambda_private_subnet.value_as_string],
            public_subnet_ids=[lambda_public_subnet.value_as_string]
        )

        # === Security Group Reference ===
        security_group = ec2.SecurityGroup.from_security_group_id(
            self, "LambdaSGRef", lambda_sg.value_as_string
        )

        # === Lambda Function ===
        lambda_func = _lambda.Function(self, "RocketChatNotifier",
            function_name="RocketChatNotifier",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_bucket(
                bucket=s3.Bucket.from_bucket_name(self, "CodeBucket", lambda_bucket.value_as_string),
                key=lambda_key.value_as_string
            ),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=128,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[security_group],
            environment={
                "WEBHOOK_PARAM": "/rocketchat/webhook_url"
            }
        )

        # === SNS Topic and Subscription ===
        sns_topic = sns.Topic(self, "DiskUsageAlertsTopic", topic_name="disk-usage-alerts")

        sns_topic.add_subscription(subs.LambdaSubscription(lambda_func))

        # === Lambda invoke permission ===
        _lambda.CfnPermission(self, "LambdaInvokePermissionForSNS",
            function_name=lambda_func.function_name,
            action="lambda:InvokeFunction",
            principal="sns.amazonaws.com",
            source_arn=sns_topic.topic_arn
        )

        # === Outputs ===
        CfnOutput(self, "LambdaFunctionArn", value=lambda_func.function_arn)
        CfnOutput(self, "LambdaExecutionRoleName", value=lambda_role.role_name)
        CfnOutput(self, "WebhookSSMParameterName", value=webhook_param.parameter_name)
        CfnOutput(self, "DiskThresholdParameterName", value=disk_threshold_param.parameter_name)
        CfnOutput(self, "SNSTopicArn", value=sns_topic.topic_arn)
