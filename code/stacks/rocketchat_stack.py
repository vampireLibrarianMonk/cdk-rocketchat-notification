from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnParameter,
    CfnOutput,
    Fn,
)
from constructs import Construct

class RocketChatStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # === Parameters ===
        subnet = CfnParameter(self, "RocketChatSubnet", type="AWS::EC2::Subnet::Id")
        security_group = CfnParameter(self, "RocketChatSG", type="AWS::EC2::SecurityGroup::Id")
        eip_allocation_id = CfnParameter(self, "RocketChatEIPAllocationId", type="String")
        key_pair = CfnParameter(self, "KeyPairName", type="AWS::EC2::KeyPair::KeyName", default="rocketchat_login")
        image_id = CfnParameter(self, "ImageId", type="String", default="ami-0c803b171269e2d72")  # us-east-2
        rocketchat_setup_s3 = CfnParameter(self, "RocketChatSetupScriptS3", type="String")
        rocketchat_setup_key = CfnParameter(self, "RocketChatSetupScriptKey", type="String")

        # === IAM Role ===
        role = iam.Role(self, "DemoEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
            ]
        )

        instance_profile = iam.CfnInstanceProfile(self, "EC2InstanceProfile", roles=[role.role_name])

        # === EC2 Instance ===
        instance = ec2.CfnInstance(self, "RocketChatInstance",
            instance_type="t3.medium",
            image_id=image_id.value_as_string,
            key_name=key_pair.value_as_string,
            subnet_id=subnet.value_as_string,
            security_group_ids=[security_group.value_as_string],
            iam_instance_profile=instance_profile.ref,
            metadata_options=ec2.CfnInstance.MetadataOptionsProperty(
                http_tokens="required",
                http_endpoint="enabled"
            ),
            tags=[{"key": "Name", "value": "rocketchat-instance"}],
            user_data=Fn.base64(
                Fn.sub(
                    """#!/bin/bash
            aws s3 cp s3://${RocketChatSetupScriptS3}/${RocketChatSetupScriptKey} /tmp/setup.sh
            chmod +x /tmp/setup.sh
            /tmp/setup.sh > /var/log/rocketchat_setup.log 2>&1""",
                    {
                        "RocketChatSetupScriptS3": rocketchat_setup_s3.value_as_string,
                        "RocketChatSetupScriptKey": rocketchat_setup_key.value_as_string
                    }
                )
            )
        )

        # === EIP Association ===
        ec2.CfnEIPAssociation(self, "RocketChatEIPAssociation",
            allocation_id=eip_allocation_id.value_as_string,
            instance_id=instance.ref
        )

        # === Output ===
        CfnOutput(self, "RocketChatInstanceId",
            value=instance.ref,
            description="EC2 instance running Rocket.Chat"
        )
