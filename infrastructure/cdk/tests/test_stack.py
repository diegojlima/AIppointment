import pytest
import json
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

from stacks.main_stack import AIppointmentStack

def test_dynamodb_tables_created():
    app = cdk.App()
    stack = AIppointmentStack(app, "TestStack", 
                             app_environment="test", 
                             project_name="test-project", 
                             whatsapp_phone_number_id="test-id", 
                             whatsapp_webhook_verify_token="test-token")
    template = Template.from_stack(stack)
    
    # Assert that we have created the DynamoDB tables
    template.resource_count_is("AWS::DynamoDB::Table", 4)
    
    # Check if appointments table has the correct properties
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "KeySchema": [
                {"AttributeName": "PhoneNumber", "KeyType": "HASH"},
                {"AttributeName": "CreatedAt", "KeyType": "RANGE"}
            ],
            "BillingMode": "PAY_PER_REQUEST"
        }
    )

def test_lambda_functions_created():
    app = cdk.App()
    stack = AIppointmentStack(app, "TestStack", 
                             app_environment="test", 
                             project_name="test-project", 
                             whatsapp_phone_number_id="test-id", 
                             whatsapp_webhook_verify_token="test-token")
    template = Template.from_stack(stack)
    
    # Assert that we have created Lambda functions
    template.resource_count_is("AWS::Lambda::Function", 5)  # 4 functional + 1 custom resource

def test_api_gateway_created():
    app = cdk.App()
    stack = AIppointmentStack(app, "TestStack", 
                             app_environment="test", 
                             project_name="test-project", 
                             whatsapp_phone_number_id="test-id", 
                             whatsapp_webhook_verify_token="test-token")
    template = Template.from_stack(stack)
    
    # Assert that we have created API Gateway
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Stage", 1)
    
def test_s3_bucket_created():
    app = cdk.App()
    stack = AIppointmentStack(app, "TestStack", 
                             app_environment="test", 
                             project_name="test-project", 
                             whatsapp_phone_number_id="test-id", 
                             whatsapp_webhook_verify_token="test-token")
    template = Template.from_stack(stack)
    
    # Assert that we have created S3 bucket for agent schema
    template.resource_count_is("AWS::S3::Bucket", 1)

def test_custom_resource_for_bedrock_agent():
    app = cdk.App()
    stack = AIppointmentStack(app, "TestStack", 
                             app_environment="test", 
                             project_name="test-project", 
                             whatsapp_phone_number_id="test-id", 
                             whatsapp_webhook_verify_token="test-token")
    template = Template.from_stack(stack)
    
    # Check that we have created a custom resource for Bedrock Agent
    template.resource_count_is("Custom::BedrockAgent", 1)
