#!/usr/bin/env python3
import os

from aws_cdk import App
from stacks.env_setup_stack import EnvSetupStack
from stacks.disk_monitor_stack import DiskMonitorStack
from stacks.rocketchat_stack import RocketChatStack
from stacks.lambda_stack import LambdaStack
from stacks.cloudwatch_alarm_stack import CloudWatchAlarmStack

app = App()

EnvSetupStack(app, "EnvSetupStack")
DiskMonitorStack(app, "DiskMonitorStack")
RocketChatStack(app, "RocketChatStack")
LambdaStack(app, "LambdaStack")
CloudWatchAlarmStack(app, "CloudWatchAlarmStack")

app.synth()
