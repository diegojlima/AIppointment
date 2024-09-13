import json
import boto3
import logging
from datetime import datetime, timedelta
import os
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_bedrock_client():
    return boto3.client('bedrock-runtime', region_name='us-west-2')

def process_message(message):
    logger.info(f"Processing message: {message}")
    bedrock = get_bedrock_client()

    # Build the messages array as per the model's requirements
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": f"""Extract appointment details from this message: "{message}"

Provide the following information in JSON format:
1. date (YYYY-MM-DD)
2. time (HH:MM)
3. purpose

If any information is missing, use null."""
                }
            ]
        }
    ]

    try:
        # Build the inference configuration
        inference_config = {
            "maxTokens": 2000,
            "temperature": 0.5
        }

        # Additional model request fields if needed
        additional_model_request_fields = {
            # Include any additional fields required by the model
            # For example: "top_k": 250
        }

        model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'

        # Log the request details
        logger.info("Invoking Bedrock model with parameters:")
        logger.info(f"Model ID: '{model_id}'")
        logger.info(f"Messages: {json.dumps(messages, indent=2)}")
        logger.info(f"Inference Config: {json.dumps(inference_config, indent=2)}")
        logger.info(f"Additional Model Request Fields: {json.dumps(additional_model_request_fields, indent=2)}")

        response = bedrock.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig=inference_config,
            additionalModelRequestParameters=additional_model_request_fields
        )

        # Log the response
        logger.info(f"Response: {json.dumps(response, indent=2)}")

        # Extract the assistant's reply
        generated_text = response.get('conversationResponse', {}).get('messages', [])[0].get('content', [])[0].get('text')

        if not generated_text:
            logger.error("No generated text found in the response.")
            return None

        logger.info(f"Generated text: {generated_text}")

        # Parse the JSON from the generated text
        appointment_details = json.loads(generated_text)
        logger.info(f"Extracted appointment details: {appointment_details}")

        return appointment_details

    except Exception as e:
        logger.error("An error occurred while processing the message", exc_info=True)
        return None
