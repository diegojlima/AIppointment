# functions/appointment-booking/src/langchain_agent_basic.py
import json
import logging
import boto3
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LangChainAgentBasic:
    """
    A basic implementation of the LangChain agent for appointment booking.
    This simplified version focuses on the core functionality of extracting
    appointment details from user messages using AWS Bedrock.
    """
    
    def __init__(self, bedrock_client=None):
        """
        Initialize the LangChain agent with AWS Bedrock
        
        Args:
            bedrock_client: Optional pre-configured Bedrock client (useful for testing)
        """
        self.region = "us-west-2"  # Default region
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name=self.region)
    
    def extract_appointment_details(self, message: str) -> Dict[str, Any]:
        """
        Extract appointment details from a message using AWS Bedrock.
        
        Args:
            message: The user message to extract details from
            
        Returns:
            A dictionary with extracted date, time, and purpose
        """
        try:
            logger.info(f"Extracting appointment details from: {message}")
            
            # Prepare the request payload for Claude 3
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Extract appointment details from this message: "{message}"

Provide the following information in JSON format:
1. date (YYYY-MM-DD)
2. time (HH:MM in 24-hour format)
3. purpose

If any information is missing, use null. Return ONLY the JSON object, nothing else."""
                            }
                        ]
                    }
                ]
            }
            
            # Call the Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if not content or not isinstance(content, list) or len(content) == 0:
                logger.error("Invalid response format from Bedrock")
                return {"date": None, "time": None, "purpose": None}
            
            # Extract the text content from the response
            text_content = next((item['text'] for item in content if item.get('type') == 'text'), None)
            
            if not text_content:
                logger.error("No text content found in the response")
                return {"date": None, "time": None, "purpose": None}
            
            # Parse the JSON from the text response
            extracted_details = json.loads(text_content)
            
            # Validate the extracted details
            if not isinstance(extracted_details, dict):
                logger.error(f"Expected a dictionary, but got {type(extracted_details)}")
                return {"date": None, "time": None, "purpose": None}
            
            # Ensure all required fields are present
            details = {
                "date": extracted_details.get("date"),
                "time": extracted_details.get("time"),
                "purpose": extracted_details.get("purpose")
            }
            
            logger.info(f"Extracted appointment details: {details}")
            return details
            
        except Exception as e:
            logger.error(f"Error extracting appointment details: {str(e)}", exc_info=True)
            return {"date": None, "time": None, "purpose": None}
