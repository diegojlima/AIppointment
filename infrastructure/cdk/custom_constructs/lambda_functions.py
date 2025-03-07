from constructs import Construct
from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    Duration,
    aws_logs as logs,
)
import os

class AppointmentBookingLambdas(Construct):
    """
    Construct for the Lambda functions used in the AIppointment application.
    """
    
    def __init__(
        self, 
        scope: Construct, 
        id: str, 
        appointments_table: dynamodb.Table,
        conversation_table: dynamodb.Table,
        messages_table: dynamodb.Table,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Define paths to Lambda source code
        src_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "functions",
            "appointment-booking",
            "src"
        )
        
        # Common Lambda role with basic permissions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant permissions to access DynamoDB tables
        appointments_table.grant_read_write_data(lambda_role)
        conversation_table.grant_read_write_data(lambda_role)
        messages_table.grant_read_write_data(lambda_role)
        
        # Add permissions for Bedrock
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock-agent:InvokeAgent"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for WhatsApp integration via AWS End User Messaging
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "connectmessagingservice:SendMessage"
                ],
                resources=["*"]
            )
        )
        
        # Common Lambda configuration
        lambda_environment = {
            "APPOINTMENTS_TABLE": appointments_table.table_name,
            "CONVERSATION_TABLE": conversation_table.table_name,
            "MESSAGES_TABLE": messages_table.table_name,
        }
        
        # Create the main Lambda function
        self.main_lambda = lambda_.Function(
            self, "MainLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=lambda_.Code.from_asset(src_path),
            environment=lambda_environment,
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create the appointment creator Lambda function
        self.appointment_creator_lambda = lambda_.Function(
            self, "AppointmentCreatorLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.appointment_creator.lambda_handler",
            code=lambda_.Code.from_asset(src_path),
            environment=lambda_environment,
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create the appointment manager Lambda function
        self.appointment_manager_lambda = lambda_.Function(
            self, "AppointmentManagerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.appointment_manager.lambda_handler",
            code=lambda_.Code.from_asset(src_path),
            environment=lambda_environment,
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create the calendar integrator Lambda function
        self.calendar_integrator_lambda = lambda_.Function(
            self, "CalendarIntegratorLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="bedrock_agent.calendar_integrator.lambda_handler",
            code=lambda_.Code.from_asset(src_path),
            environment=lambda_environment,
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            log_retention=logs.RetentionDays.ONE_WEEK
        )
