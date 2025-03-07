from constructs import Construct
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_iam as iam,
)

class ApiGatewayConstruct(Construct):
    """
    Construct for the API Gateway configuration.
    """
    
    def __init__(
        self,
        scope: Construct,
        id: str,
        main_lambda: lambda_.Function,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Create the REST API
        self.api = apigateway.RestApi(
            self, "AIppointmentApi",
            rest_api_name="AIppointment API",
            description="API for the AIppointment application",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
            endpoint_types=[apigateway.EndpointType.REGIONAL],
        )
        
        # WhatsApp webhook endpoint
        whatsapp_resource = self.api.root.add_resource("whatsapp-webhook")
        
        # POST method for WhatsApp webhook
        whatsapp_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                main_lambda,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "'application/json'",
                        }
                    )
                ]
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True,
                    }
                )
            ]
        )
        
        # GET method for WhatsApp webhook verification
        whatsapp_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                main_lambda,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "'text/plain'",
                        }
                    )
                ]
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True,
                    }
                )
            ]
        )
        
        # Create a booking resource
        booking_resource = self.api.root.add_resource("book")
        
        # POST method for booking endpoint
        booking_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                main_lambda,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Content-Type": "'application/json'",
                        }
                    )
                ]
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True,
                    }
                )
            ]
        )
