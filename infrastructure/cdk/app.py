#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from stacks.main_stack import AIppointmentStack

# Define environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", ""),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-west-2")
)

app = App()

AIppointmentStack(
    app, 
    "AIppointmentStack",
    env=env,
    description="AIppointment application infrastructure (migrated from Terraform)",
)

app.synth()
