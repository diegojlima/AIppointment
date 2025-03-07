from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_iam as iam,
    aws_logs as logs,
    custom_resources as cr,
    Duration,
    RemovalPolicy,
    CustomResource,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
import os

class AIppointmentStack(Stack):
    """
    Main CDK stack for the AIppointment application, migrated from Terraform.
    """
    
    def __init__(self, scope: Construct, construct_id: str, environment: str, project_name: str, whatsapp_phone_number_id: str = None, whatsapp_webhook_verify_token: str = None, foundation_model_id: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store parameters
        self.environment = environment
        self.project_name = project_name
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_webhook_verify_token = whatsapp_webhook_verify_token
        self.foundation_model_id = foundation_model_id or "anthropic.claude-3-haiku-20240307-v1:0"
        
        # Create DynamoDB tables
        appointments_table = dynamodb.Table(
            self, "AppointmentsTable",
            table_name=f"{project_name}-appointments",
            partition_key=dynamodb.Attribute(
                name="PhoneNumber",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="CreatedAt",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Calendar credentials table
        calendar_credentials_table = dynamodb.Table(
            self, "CalendarCredentialsTable",
            table_name=f"{project_name}-calendar-credentials",
            partition_key=dynamodb.Attribute(
                name="provider",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Conversation history table
        conversation_history_table = dynamodb.Table(
            self, "ConversationHistoryTable",
            table_name=f"{project_name}-conversation-history",
            partition_key=dynamodb.Attribute(
                name="conversationId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Add GSI for senderId access pattern
        conversation_history_table.add_global_secondary_index(
            index_name="SenderIdIndex",
            partition_key=dynamodb.Attribute(
                name="senderId",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Conversation messages table
        conversation_messages_table = dynamodb.Table(
            self, "ConversationMessagesTable",
            table_name=f"{project_name}-conversation-messages",
            partition_key=dynamodb.Attribute(
                name="messageId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="conversationId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # HTTP API Gateway
        http_api = apigatewayv2.HttpApi(
            self, "HttpApi",
            api_name=f"{project_name}-api",
        )
        
        # Create API Gateway stage
        stage = apigatewayv2.HttpStage(
            self, "ApiStage",
            http_api=http_api,
            stage_name=environment,
            auto_deploy=True,
        )
        
        # Common Lambda configuration
        lambda_code_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "functions",
            "appointment-booking",
            "src"
        )
        
        # Common Lambda role
        lambda_role = iam.Role(
            self, "LambdaRole",
            role_name=f"{project_name}-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add DynamoDB permissions
        appointments_table.grant_read_write_data(lambda_role)
        calendar_credentials_table.grant_read_write_data(lambda_role)
        conversation_history_table.grant_read_write_data(lambda_role)
        conversation_messages_table.grant_read_write_data(lambda_role)
        
        # Add Bedrock permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:ListFoundationModels",
                    "bedrock-runtime:Converse",
                    "bedrock-runtime:ConverseStream"
                ],
                resources=["*"]
            )
        )
        
        # Create main Lambda function
        booking_lambda = lambda_.Function(
            self, "BookingLambda",
            function_name=f"{project_name}-booking",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            environment={
                "DYNAMODB_TABLE": appointments_table.table_name,
                "CONVERSATION_TABLE": conversation_history_table.table_name,
                "MESSAGES_TABLE": conversation_messages_table.table_name,
                "WHATSAPP_PHONE_NUMBER_ID": self.whatsapp_phone_number_id or "",
                "WHATSAPP_WEBHOOK_VERIFY_TOKEN": self.whatsapp_webhook_verify_token or "",
                "BEDROCK_MODEL_ID": self.foundation_model_id,
                "ENVIRONMENT": self.environment,
            },
            timeout=Duration.seconds(30),
            memory_size=128,
            role=lambda_role,
        )
        
        # Create HTTP API integration
        booking_lambda_integration = HttpLambdaIntegration(
            "BookingIntegration",
            booking_lambda
        )
        
        # Add route to API Gateway
        http_api.add_routes(
            path="/book-appointment",
            methods=[apigatewayv2.HttpMethod.POST],
            integration=booking_lambda_integration,
        )
        
        # Grant API Gateway permission to invoke Lambda
        booking_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api.api_id}/*/*/*",
        )
        
        # Create Bedrock Agent related resources
        from infrastructure.cdk.constructs.bedrock_agent import BedrockAgentConstruct
        
        bedrock_agent_construct = BedrockAgentConstruct(
            self, "BedrockAgent",
            schema_bucket=s3.Bucket(
                self, "SchemasBucket",
                bucket_name=f"{project_name}-schemas-{environment}",
                removal_policy=RemovalPolicy.RETAIN
            ),
            appointment_creator_lambda=lambda_.Function(
                self, "AppointmentCreatorLambda",
                function_name=f"{project_name}-appointment-creator-{environment}",
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler="bedrock_agent.appointment_creator.lambda_handler",
                code=lambda_.Code.from_asset(lambda_code_path),
                timeout=Duration.seconds(30),
                memory_size=256,
                role=lambda_role
            ),
            appointment_manager_lambda=lambda_.Function(
                self, "AppointmentManagerLambda",
                function_name=f"{project_name}-appointment-manager-{environment}",
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler="bedrock_agent.appointment_manager.lambda_handler",
                code=lambda_.Code.from_asset(lambda_code_path),
                timeout=Duration.seconds(30),
                memory_size=256,
                role=lambda_role
            ),
            calendar_integrator_lambda=lambda_.Function(
                self, "CalendarIntegratorLambda",
                function_name=f"{project_name}-calendar-integrator-{environment}",
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler="bedrock_agent.calendar_integrator.lambda_handler",
                code=lambda_.Code.from_asset(lambda_code_path),
                timeout=Duration.seconds(30),
                memory_size=256,
                role=lambda_role
            ),
            foundation_model_id=self.foundation_model_id
        )
        
        # Add stack outputs
        from aws_cdk import CfnOutput
        
        CfnOutput(self, "BedrockAgentId",
            value=bedrock_agent_construct.agent_id,
            description="ID of the Bedrock Agent",
            export_name=f"{project_name}-agent-id-{environment}"
        )
        
        CfnOutput(self, "BedrockAgentAliasId",
            value=bedrock_agent_construct.agent_alias_id,
            description="ID of the Bedrock Agent Alias",
            export_name=f"{project_name}-agent-alias-id-{environment}"
        )
        
        CfnOutput(self, "ApiGatewayUrl",
            value=http_api.api_endpoint,
            description="URL of the API Gateway",
            export_name=f"{project_name}-api-url-{environment}"
        )
    
    def create_bedrock_agent_resources(
        self,
        project_name: str,
        environment: str,
        appointments_table: dynamodb.Table,
        calendar_credentials_table: dynamodb.Table,
        lambda_code_path: str,
        lambda_role: iam.Role,
    ):
        # Create S3 bucket for agent schemas
        schema_bucket = s3.Bucket(
            self, "BedrockSchemasBucket",
            bucket_name=f"{project_name}-bedrock-schema-{environment}",
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        
        # Get schema path
        schema_dir_path = os.path.join(
            lambda_code_path,
            "bedrock_agent",
            "schema"
        )
        
        # Deploy schema to S3
        schema_deployment = s3_deployment.BucketDeployment(
            self, "SchemaDeployment",
            sources=[s3_deployment.Source.asset(schema_dir_path)],
            destination_bucket=schema_bucket,
        )
        
        # Create Lambda functions for Bedrock Agent action groups
        appointment_creator_lambda = lambda_.Function(
            self, "AppointmentCreatorLambda",
            function_name=f"{project_name}-appointment-creator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.appointment_creator.lambda_handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            environment={
                "DYNAMODB_TABLE": appointments_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )
        
        appointment_manager_lambda = lambda_.Function(
            self, "AppointmentManagerLambda",
            function_name=f"{project_name}-appointment-manager",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.appointment_manager.lambda_handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            environment={
                "DYNAMODB_TABLE": appointments_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )
        
        calendar_integrator_lambda = lambda_.Function(
            self, "CalendarIntegratorLambda",
            function_name=f"{project_name}-calendar-integrator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.calendar_integrator.lambda_handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            environment={
                "DYNAMODB_TABLE": appointments_table.table_name,
                "LOG_LEVEL": "INFO",
                "DEFAULT_CALENDAR_PROVIDER": "GOOGLE",
                "CALENDAR_CREDENTIALS_TABLE": calendar_credentials_table.table_name,
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )
        
        # Create IAM role for Bedrock Agent
        bedrock_agent_role = iam.Role(
            self, "BedrockAgentRole",
            role_name=f"{project_name}-bedrock-agent-role-{environment}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )
        
        # Add Lambda invoke permissions to role
        bedrock_agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[
                    appointment_creator_lambda.function_arn,
                    appointment_manager_lambda.function_arn,
                    calendar_integrator_lambda.function_arn,
                ]
            )
        )
        
        # Add S3 read permissions to role
        schema_bucket.grant_read(bedrock_agent_role)
        
        # Create Custom Resource for Bedrock Agent creation
        # Since CDK doesn't have native L2 constructs for Bedrock Agents yet
        bedrock_agent_provider = self.create_bedrock_agent_provider()
        
        # Create the Bedrock Agent using a custom resource
        agent_resource = CustomResource(
            self, "BedrockAgentResource",
            service_token=bedrock_agent_provider.service_token,
            properties={
                "AgentName": f"{project_name}-agent-{environment}",
                "AgentDescription": f"Agent for handling appointment scheduling - {environment}",
                "AgentRoleArn": bedrock_agent_role.role_arn,
                "FoundationModel": self.foundation_model_id,
                "Instruction": """
                    You are an appointment scheduling assistant integrated with WhatsApp. 
                    Your primary job is to help users schedule, reschedule, and cancel appointments.
                    
                    Key tasks you can perform:
                    1. Check availability for a specific date
                    2. Create new appointments
                    3. View existing appointments
                    4. Reschedule appointments
                    5. Cancel appointments
                    
                    When talking to users:
                    - Be friendly and conversational
                    - Ask for clarification when needed
                    - Confirm details before making changes
                    - Offer alternative time slots if requested times are unavailable
                    - Send confirmation messages with appointment details
                    
                    Available time slots are hourly from 9 AM to 5 PM, Monday through Friday.
                    Appointments are 1 hour by default unless specified otherwise.
                    
                    Use the available action groups to perform calendar operations and appointment management.
                """,
                "SchemaS3BucketName": schema_bucket.bucket_name,
                "SchemaS3ObjectKey": "agent_schema.json",
                "ActionGroups": [
                    {
                        "ActionGroupName": "AppointmentCreator",
                        "Description": "Creates appointments and checks availability",
                        "LambdaArn": appointment_creator_lambda.function_arn,
                    },
                    {
                        "ActionGroupName": "AppointmentManager",
                        "Description": "Manages existing appointments (get, reschedule, cancel)",
                        "LambdaArn": appointment_manager_lambda.function_arn,
                    },
                    {
                        "ActionGroupName": "CalendarIntegrator",
                        "Description": "Integrates with external calendar systems",
                        "LambdaArn": calendar_integrator_lambda.function_arn,
                    }
                ],
                "AliasName": environment,
                "AliasDescription": f"{project_name} agent alias for {environment} environment",
            },
            resource_type="Custom::BedrockAgent",
        )
    
    def create_bedrock_agent_provider(self) -> cr.Provider:
        """
        Create a custom resource provider Lambda function that will create
        the Bedrock Agent using the AWS SDK.
        """
        # Create the Lambda function code
        function_code = '''
import boto3
import cfnresponse
import os
import time
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent = boto3.client('bedrock-agent')

def on_event(event, context):
    logger.info(f"Event: {event}")
    request_type = event['RequestType']
    
    if request_type == 'Create':
        return on_create(event, context)
    elif request_type == 'Update':
        return on_update(event, context)
    elif request_type == 'Delete':
        return on_delete(event, context)
    else:
        raise Exception(f"Invalid request type: {request_type}")

def on_create(event, context):
    props = event['ResourceProperties']
    
    # Create the agent
    try:
        agent_response = bedrock_agent.create_agent(
            agentName=props['AgentName'],
            description=props.get('AgentDescription', ''),
            instruction=props['Instruction'],
            foundationModel=props['FoundationModel'],
            agentResourceRoleArn=props['AgentRoleArn'],
            customerEncryptionKeyArn=props.get('CustomerEncryptionKeyArn', ''),
            idleSessionTTLInSeconds=int(props.get('IdleSessionTTL', 3600))
        )
        
        agent_id = agent_response['agent']['agentId']
        logger.info(f"Created agent with ID: {agent_id}")
        
        # Wait for the agent to be available
        wait_for_agent(agent_id)
        
        # Create action groups
        for action_group in props.get('ActionGroups', []):
            action_group_response = bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=action_group['ActionGroupName'],
                description=action_group.get('Description', ''),
                actionGroupExecutor=json.dumps({
                    'lambda': {
                        'lambdaArn': action_group['LambdaArn']
                    }
                }),
                apiSchema=json.dumps({
                    's3': {
                        's3BucketName': props['SchemaS3BucketName'],
                        's3ObjectKey': props['SchemaS3ObjectKey']
                    }
                })
            )
            logger.info(f"Created action group: {action_group_response['actionGroupId']}")
        
        # Prepare the agent
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"Prepared agent: {prepare_response}")
        
        # Wait for preparation to complete
        wait_for_preparation(agent_id)
        
        # Create alias
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName=props['AliasName'],
            description=props.get('AliasDescription', '')
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        logger.info(f"Created agent alias with ID: {alias_id}")
        
        return {
            'PhysicalResourceId': agent_id,
            'Data': {
                'AgentId': agent_id,
                'AgentAliasId': alias_id
            }
        }
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise e

def on_update(event, context):
    # Handle updates to the agent
    props = event['ResourceProperties']
    physical_id = event['PhysicalResourceId']
    
    try:
        # Update the agent properties
        agent_response = bedrock_agent.update_agent(
            agentId=physical_id,
            agentName=props['AgentName'],
            description=props.get('AgentDescription', ''),
            instruction=props['Instruction'],
            agentResourceRoleArn=props['AgentRoleArn']
        )
        
        logger.info(f"Updated agent with ID: {physical_id}")
        
        # Get existing action groups
        action_groups_response = bedrock_agent.list_agent_action_groups(
            agentId=physical_id,
            agentVersion='DRAFT'
        )
        
        existing_action_groups = {
            ag['actionGroupName']: ag['actionGroupId'] 
            for ag in action_groups_response.get('actionGroupSummaries', [])
        }
        
        # Update or create action groups
        for action_group in props.get('ActionGroups', []):
            action_group_name = action_group['ActionGroupName']
            
            if action_group_name in existing_action_groups:
                # Update existing action group
                bedrock_agent.update_agent_action_group(
                    agentId=physical_id,
                    agentVersion='DRAFT',
                    actionGroupId=existing_action_groups[action_group_name],
                    actionGroupName=action_group_name,
                    description=action_group.get('Description', ''),
                    actionGroupExecutor=json.dumps({
                        'lambda': {
                            'lambdaArn': action_group['LambdaArn']
                        }
                    }),
                    apiSchema=json.dumps({
                        's3': {
                            's3BucketName': props['SchemaS3BucketName'],
                            's3ObjectKey': props['SchemaS3ObjectKey']
                        }
                    })
                )
                logger.info(f"Updated action group: {action_group_name}")
            else:
                # Create new action group
                bedrock_agent.create_agent_action_group(
                    agentId=physical_id,
                    agentVersion='DRAFT',
                    actionGroupName=action_group_name,
                    description=action_group.get('Description', ''),
                    actionGroupExecutor=json.dumps({
                        'lambda': {
                            'lambdaArn': action_group['LambdaArn']
                        }
                    }),
                    apiSchema=json.dumps({
                        's3': {
                            's3BucketName': props['SchemaS3BucketName'],
                            's3ObjectKey': props['SchemaS3ObjectKey']
                        }
                    })
                )
                logger.info(f"Created action group: {action_group_name}")
        
        # Prepare the agent
        prepare_response = bedrock_agent.prepare_agent(agentId=physical_id)
        logger.info(f"Prepared agent after update: {prepare_response}")
        
        # Wait for preparation to complete
        wait_for_preparation(physical_id)
        
        # Get existing aliases
        aliases_response = bedrock_agent.list_agent_aliases(agentId=physical_id)
        
        existing_aliases = {
            alias['agentAliasName']: alias['agentAliasId'] 
            for alias in aliases_response.get('agentAliasSummaries', [])
        }
        
        alias_name = props['AliasName']
        if alias_name in existing_aliases:
            # Update existing alias
            alias_response = bedrock_agent.update_agent_alias(
                agentId=physical_id,
                agentAliasId=existing_aliases[alias_name],
                agentAliasName=alias_name,
                description=props.get('AliasDescription', '')
            )
            logger.info(f"Updated agent alias: {alias_name}")
        else:
            # Create new alias
            alias_response = bedrock_agent.create_agent_alias(
                agentId=physical_id,
                agentAliasName=alias_name,
                description=props.get('AliasDescription', '')
            )
            logger.info(f"Created agent alias: {alias_name}")
        
        return {
            'PhysicalResourceId': physical_id,
            'Data': {
                'AgentId': physical_id,
                'AgentAliasId': existing_aliases.get(alias_name, alias_response['agentAlias']['agentAliasId'])
            }
        }
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise e

def on_delete(event, context):
    physical_id = event['PhysicalResourceId']
    
    try:
        # Get agent aliases
        aliases_response = bedrock_agent.list_agent_aliases(agentId=physical_id)
        
        # Delete aliases
        for alias in aliases_response.get('agentAliasSummaries', []):
            bedrock_agent.delete_agent_alias(
                agentId=physical_id,
                agentAliasId=alias['agentAliasId']
            )
            logger.info(f"Deleted agent alias: {alias['agentAliasId']}")
        
        # Delete the agent
        bedrock_agent.delete_agent(agentId=physical_id)
        logger.info(f"Deleted agent: {physical_id}")
        
        return {
            'PhysicalResourceId': physical_id
        }
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        # Don't fail on deletion errors
        return {
            'PhysicalResourceId': physical_id
        }

def wait_for_agent(agent_id, max_retries=30, retry_interval=10):
    """Wait for the agent to be available."""
    for i in range(max_retries):
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['status']
            logger.info(f"Agent status: {status}")
            
            if status == 'PREPARED':
                return
            
            if status in ['FAILED', 'FAILED_CREATION', 'DELETING', 'DELETED']:
                raise Exception(f"Agent creation failed with status: {status}")
            
            time.sleep(retry_interval)
        except Exception as e:
            logger.error(f"Error checking agent status: {str(e)}")
            time.sleep(retry_interval)
    
    raise Exception(f"Timed out waiting for agent to become available")

def wait_for_preparation(agent_id, max_retries=30, retry_interval=10):
    """Wait for the agent preparation to complete."""
    for i in range(max_retries):
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['status']
            logger.info(f"Agent preparation status: {status}")
            
            if status == 'PREPARED':
                return
            
            if status in ['FAILED', 'FAILED_CREATION', 'DELETING', 'DELETED']:
                raise Exception(f"Agent preparation failed with status: {status}")
            
            time.sleep(retry_interval)
        except Exception as e:
            logger.error(f"Error checking agent preparation status: {str(e)}")
            time.sleep(retry_interval)
    
    raise Exception(f"Timed out waiting for agent preparation to complete")

def handler(event, context):
    try:
        logger.info('Received event: %s' % json.dumps(event))
        result = on_event(event, context)
        logger.info('Result: %s' % json.dumps(result))
        
        cfnresponse.send(
            event, 
            context, 
            cfnresponse.SUCCESS, 
            result.get('Data', {}), 
            result.get('PhysicalResourceId')
        )
    except Exception as e:
        logger.error('Failed to process: %s' % e)
        cfnresponse.send(
            event, 
            context, 
            cfnresponse.FAILED, 
            {}, 
            event.get('PhysicalResourceId', context.log_stream_name),
            str(e)
        )
        '''
        
        # Create Lambda function for custom resource
        provider_function = lambda_.Function(
            self, "BedrockAgentProviderFunction",
            function_name="bedrock-agent-provider",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_inline(function_code),
            timeout=Duration.minutes(15),
            memory_size=512,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        # Add required permissions
        provider_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agent:CreateAgent",
                    "bedrock-agent:UpdateAgent",
                    "bedrock-agent:DeleteAgent",
                    "bedrock-agent:PrepareAgent",
                    "bedrock-agent:GetAgent",
                    "bedrock-agent:CreateAgentActionGroup",
                    "bedrock-agent:UpdateAgentActionGroup",
                    "bedrock-agent:DeleteAgentActionGroup",
                    "bedrock-agent:ListAgentActionGroups",
                    "bedrock-agent:CreateAgentAlias",
                    "bedrock-agent:UpdateAgentAlias",
                    "bedrock-agent:DeleteAgentAlias",
                    "bedrock-agent:ListAgentAliases",
                ],
                resources=["*"],
            )
        )
        
        # Create the provider
        provider = cr.Provider(
            self, "BedrockAgentProvider",
            on_event_handler=provider_function,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        return provider
