from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnParameter,
    CfnOutput,
    Fn,
)
from constructs import Construct

class DiskMonitorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # === Parameters ===
        disk_monitor_subnet = CfnParameter(self, "DiskMonitorSubnet", type="AWS::EC2::Subnet::Id")
        disk_monitor_sg = CfnParameter(self, "DiskMonitorSG", type="AWS::EC2::SecurityGroup::Id")
        key_pair_name = CfnParameter(self, "DiskMonitorKeyPair", type="AWS::EC2::KeyPair::KeyName", default="ebs_alert_tester")
        image_id = CfnParameter(self, "DiskMonitorImageId", type="String", default="ami-0c803b171269e2d72") 
        disk_monitor_setup_s3 = CfnParameter(self, "DiskMonitorSetupS3", type="String")
        disk_monitor_setup_key = CfnParameter(self, "DiskMonitorSetupKey", type="String")
        disk_fill_script_s3 = CfnParameter(self, "DiskFillScriptS3", type="String")
        disk_fill_script_key = CfnParameter(self, "DiskFillScriptKey", type="String")

        # === IAM Role ===
        demo_role = iam.Role(self, "DemoEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
            ]
        )

        instance_profile = iam.CfnInstanceProfile(self, "EC2InstanceProfile",
            roles=[demo_role.role_name]
        )

        # === EC2 Instance ===
        ec2_instance = ec2.CfnInstance(self, "EBSAlertTestEC2",
            instance_type="t3.micro",
            image_id=image_id.value_as_string,
            key_name=key_pair_name.value_as_string,
            subnet_id=disk_monitor_subnet.value_as_string,
            security_group_ids=[disk_monitor_sg.value_as_string],
            iam_instance_profile=instance_profile.ref,
            tags=[{"key": "Name", "value": "EBSAlertTestEC2"}],
            user_data=Fn.base64(
                Fn.sub(
                    """#!/bin/bash
            aws s3 cp s3://${DiskMonitorSetupS3}/${DiskMonitorSetupKey} /tmp/setup.sh
            chmod +x /tmp/setup.sh
            /tmp/setup.sh

            aws s3 cp s3://${DiskFillScriptS3}/${DiskFillScriptKey} /usr/local/bin/disk_fill_tool.sh
            chmod +x /usr/local/bin/disk_fill_tool.sh
            """,
                    {
                        "DiskMonitorSetupS3": disk_monitor_setup_s3.value_as_string,
                        "DiskMonitorSetupKey": disk_monitor_setup_key.value_as_string,
                        "DiskFillScriptS3": disk_fill_script_s3.value_as_string,
                        "DiskFillScriptKey": disk_fill_script_key.value_as_string
                    }
                )
            )
        )
            
        # === EBS Volumes ===
        az = Fn.select(0, Fn.get_azs(""))

        volume1 = ec2.CfnVolume(self, "EBSVolume1",
            availability_zone=az,
            size=10,
            volume_type="gp3",
            tags=[{"key": "Name", "value": "EBSVolume1"}]
        )

        volume2 = ec2.CfnVolume(self, "EBSVolume2",
            availability_zone=az,
            size=10,
            volume_type="gp3",
            tags=[{"key": "Name", "value": "EBSVolume2"}]
        )

        volume3 = ec2.CfnVolume(self, "EBSVolume3",
            availability_zone=az,
            size=10,
            volume_type="gp3",
            tags=[{"key": "Name", "value": "EBSVolume3"}]
        )

        # === Attach Volumes ===
        ec2.CfnVolumeAttachment(self, "AttachVolume1",
            instance_id=ec2_instance.ref,
            volume_id=volume1.ref,
            device="/dev/xvdf"
        )

        ec2.CfnVolumeAttachment(self, "AttachVolume2",
            instance_id=ec2_instance.ref,
            volume_id=volume2.ref,
            device="/dev/xvdg"
        )

        ec2.CfnVolumeAttachment(self, "AttachVolume3",
            instance_id=ec2_instance.ref,
            volume_id=volume3.ref,
            device="/dev/xvdh"
        )

        # === Outputs ===
        CfnOutput(self, "EBSAlertTestEC2Id",
            value=ec2_instance.ref,
            description="EC2 instance for Disk Monitor"
        )
