#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from stacks.main_stack import AIppointmentStack

# Get environment from context or default to 'dev'
app = App()
environment = app.node.try_get_context('environment') or 'dev'
project_name = app.node.try_get_context('projectName') or 'aippointment'

# Define AWS environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", ""),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-west-2")
)

# Create the main stack
stack = AIppointmentStack(
    app, 
    "AIppointmentStack",
    env=env,
    description=f"AIppointment application infrastructure for {environment} environment",
    environment=environment,
    project_name=project_name,
    # Pass other context values to the stack
    whatsapp_phone_number_id=app.node.try_get_context('whatsappPhoneNumberId'),
    whatsapp_webhook_verify_token=app.node.try_get_context('whatsappWebhookVerifyToken'),
    foundation_model_id=app.node.try_get_context('foundationModelId') or "anthropic.claude-3-haiku-20240307-v1:0",
)

# Add tags to all resources in the stack
stack.tags.set_tag("Environment", environment)
stack.tags.set_tag("Project", project_name)
stack.tags.set_tag("ManagedBy", "CDK")

app.synth()
