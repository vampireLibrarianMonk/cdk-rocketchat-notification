from aws_cdk import (
    Stack,
    Token,
    aws_cloudwatch as cloudwatch,
    CfnParameter,
)
from constructs import Construct

class CloudWatchAlarmStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # === Parameters ===
        instance_id = CfnParameter(self, "InstanceId", type="String")
        sns_topic_arn = CfnParameter(self, "DiskUsageAlertsTopic", type="String")
        disk_threshold_param = CfnParameter(self, "DiskThresholdParamName", type="AWS::SSM::Parameter::Value<String>",
                                            default="/diskmonitor/threshold/percent")

        # === Common alarm builder ===
        def create_alarm(volume: str):
            return cloudwatch.CfnAlarm(self, f"DiskAlarm{volume}",
                alarm_name=f"mnt_{volume}_high_disk_usage",
                namespace="CWAgent",
                metric_name="disk_used_percent",
                statistic="Average",
                period=60,
                evaluation_periods=1,
                threshold=Token.as_number(disk_threshold_param.value_as_string),
                comparison_operator="GreaterThanThreshold",
                dimensions=[
                    cloudwatch.CfnAlarm.DimensionProperty(name="path", value=f"/mnt/{volume}"),
                    cloudwatch.CfnAlarm.DimensionProperty(name="InstanceId", value=instance_id.value_as_string),
                    cloudwatch.CfnAlarm.DimensionProperty(name="fstype", value="ext4"),
                ],
                alarm_actions=[sns_topic_arn.value_as_string],
                treat_missing_data="notBreaching",
                unit="Percent"
            )

        # Volumes: vol1, vol2, vol3
        for volume in ["vol1", "vol2", "vol3"]:
            create_alarm(volume)
