from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_lambda as lambda_,
    CustomResource,
    custom_resources as cr,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    Stack,
)
import os

class BedrockAgentConstruct(Construct):
    """
    Construct for creating a Bedrock Agent with action groups.
    
    Note: As of the current CDK version, there's no L2 construct for Bedrock Agents,
    so we're using CustomResource to create the agent.
    """
    
    def __init__(
        self,
        scope: Construct,
        id: str,
        schema_bucket: s3.Bucket,
        appointment_creator_lambda: lambda_.Function,
        appointment_manager_lambda: lambda_.Function,
        calendar_integrator_lambda: lambda_.Function,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Get schema path
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "functions",
            "appointment-booking",
            "src",
            "bedrock_agent",
            "schema",
            "agent_schema.json"
        )
        
        # Upload schema to S3
        schema_deployment = s3_deployment.BucketDeployment(
            self, "SchemaDeployment",
            sources=[s3_deployment.Source.asset(os.path.dirname(schema_path))],
            destination_bucket=schema_bucket,
            destination_key_prefix="schema",
        )
        
        # IAM role for the agent
        agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )
        
        # Add policy to invoke Lambda functions
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[
                    appointment_creator_lambda.function_arn,
                    appointment_manager_lambda.function_arn,
                    calendar_integrator_lambda.function_arn,
                ]
            )
        )
        
        # Add policy to access S3 bucket
        schema_bucket.grant_read(agent_role)
        
        # Create a Lambda function for the custom resource to create the Bedrock Agent
        bedrock_agent_provider = self.create_custom_resource_provider()
        
        # Create the Bedrock Agent using a custom resource
        agent_resource = CustomResource(
            self, "BedrockAgentResource",
            service_token=bedrock_agent_provider.service_token,
            properties={
                "AgentName": "AIppointmentAgent",
                "AgentDescription": "Agent for handling appointment scheduling",
                "AgentRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-haiku-20240307-v1:0",
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
                "SchemaS3ObjectKey": "schema/agent_schema.json",
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
                "AliasName": "prod",
                "AliasDescription": "Production alias for the appointment agent",
            },
            resource_type="Custom::BedrockAgent",
        )
        
        # Make sure schema is deployed before creating the agent
        agent_resource.node.add_dependency(schema_deployment)
        
        # Export important resources
        self.agent_role = agent_role
        self.agent_resource = agent_resource
    
    def create_custom_resource_provider(self) -> cr.Provider:
        """
        Create a custom resource provider Lambda function that will create
        the Bedrock Agent using the AWS SDK.
        """
        # Create the Lambda function code
        function_code = """
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
        """
        
        # Create Lambda function for custom resource
        provider_function = lambda_.Function(
            self, "BedrockAgentProviderFunction",
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
