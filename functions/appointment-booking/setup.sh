#!/bin/bash

# AIppointment Setup Script
# This script helps set up the required AWS infrastructure for AIppointment

echo "Starting AIppointment setup..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
if [ $? -ne 0 ]; then
    echo "Failed to get AWS account ID. Make sure you have configured AWS CLI correctly."
    exit 1
fi

echo "Using AWS Account ID: $ACCOUNT_ID"

# Set variables
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="us-west-2"
    echo "No region found in AWS CLI config. Using default: $REGION"
fi

# Create DynamoDB tables
echo "Creating DynamoDB tables..."

echo "Creating Appointments table..."
aws dynamodb create-table \
  --table-name Appointments \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "Creating ConversationHistory table..."
aws dynamodb create-table \
  --table-name ConversationHistory \
  --attribute-definitions \
    AttributeName=conversationId,AttributeType=S \
    AttributeName=senderId,AttributeType=S \
  --key-schema AttributeName=conversationId,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=SenderIdIndex,KeySchema=["{AttributeName=senderId,KeyType=HASH}"],Projection="{ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "Creating ConversationHistoryMessages table..."
aws dynamodb create-table \
  --table-name ConversationHistoryMessages \
  --attribute-definitions \
    AttributeName=messageId,AttributeType=S \
    AttributeName=conversationId,AttributeType=S \
  --key-schema \
    AttributeName=messageId,KeyType=HASH \
    AttributeName=conversationId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

# Create IAM role for Lambda
echo "Creating IAM role for Lambda..."
ROLE_NAME="AIppointment-LambdaRole"

# Check if role already exists
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null)
if [ $? -ne 0 ]; then
    # Create trust policy document
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    ROLE_ARN=$(aws iam create-role \
      --role-name $ROLE_NAME \
      --assume-role-policy-document file://trust-policy.json \
      --query 'Role.Arn' \
      --output text)
    
    rm trust-policy.json
    
    # Attach policies to the role
    aws iam attach-role-policy \
      --role-name $ROLE_NAME \
      --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
      --role-name $ROLE_NAME \
      --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
    
    aws iam attach-role-policy \
      --role-name $ROLE_NAME \
      --policy-arn arn:aws:iam::aws:policy/AmazonBedrockAgentFullAccess
    
    aws iam attach-role-policy \
      --role-name $ROLE_NAME \
      --policy-arn arn:aws:iam::aws:policy/AmazonConnectUserMessagingFullAccess

    echo "Created IAM role: $ROLE_ARN"
else
    echo "Using existing IAM role: $ROLE_ARN"
fi

echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Create a Bedrock Agent in the AWS console using the schema in bedrock_agent/schema/agent_schema.json"
echo "2. Set up AWS End User Messaging for WhatsApp"
echo "3. Deploy the Lambda function"
echo "4. Configure calendar integration"
echo ""
echo "See the README.md file for detailed instructions."
