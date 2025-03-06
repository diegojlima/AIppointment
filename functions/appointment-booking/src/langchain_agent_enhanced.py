# functions/appointment-booking/src/langchain_agent_enhanced.py
import json
import logging
import boto3
from typing import Dict, Any, List

# Import LangChain components - we'll need to ensure these are installed
try:
    from langchain_aws import ChatBedrock
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import SystemMessage, HumanMessage
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain packages not available. Using fallback methods.")

logger = logging.getLogger(__name__)

class LangChainAgentEnhanced:
    """
    Enhanced implementation of a LangChain agent for appointment booking.
    Uses LangChain's ChatBedrock and conversation memory for improved interactions.
    """
    
    def __init__(self, bedrock_client=None, session_id=None):
        """
        Initialize the LangChain agent with AWS Bedrock and conversation memory
        
        Args:
            bedrock_client: Optional pre-configured Bedrock client (useful for testing)
            session_id: Optional session identifier for maintaining conversation history
        """
        self.region = "us-west-2"  # Default region
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name=self.region)
        self.session_id = session_id or "default-session"
        
        # Initialize memory
        if LANGCHAIN_AVAILABLE:
            self.memory = ConversationBufferMemory(memory_key="chat_history")
            self.fallback_memory = []  # For testing without actual LangChain
        else:
            self.memory = []  # Simple list-based memory fallback
        
        # Initialize LangChain components if available
        if LANGCHAIN_AVAILABLE:
            self.llm = self._create_llm()
            logger.info("LangChain integration initialized successfully")
        else:
            logger.warning("LangChain not available. Using basic implementation.")
    
    def _create_llm(self):
        """Create and configure the LangChain ChatBedrock instance"""
        if not LANGCHAIN_AVAILABLE:
            return None
            
        return ChatBedrock(
            client=self.bedrock_client,
            model_id=self.model_id,
            model_kwargs={
                "max_tokens": 1000,
                "temperature": 0.0
            }
        )
    
    def _create_extraction_chain(self):
        """Create a chain for extracting appointment details"""
        if not LANGCHAIN_AVAILABLE:
            return None
            
        system_template = """You are an AI assistant that extracts appointment details from user messages.
Your task is to identify the date, time, and purpose of an appointment from the user's message.
Respond with ONLY a valid JSON object containing:
- date: in YYYY-MM-DD format (or null if not found)
- time: in HH:MM 24-hour format (or null if not found)
- purpose: the purpose of the appointment (or null if not found)

For example, if the user says "I need a dental checkup next Wednesday at 2pm",
you should respond with something like:
{"date": "2023-09-20", "time": "14:00", "purpose": "dental checkup"}

Only return the JSON object, no other text."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", "{input}")
        ])
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt
        )
    
    def add_to_memory(self, role: str, content: str):
        """Add a message to the conversation memory"""
        if LANGCHAIN_AVAILABLE:
            # Update both memory types for testing purposes
            if role == "user":
                self.memory.save_context({"input": content}, {"output": ""})
            else:
                # Update the output for the assistant
                self.memory.save_context({"input": ""}, {"output": content})
                
            # Always update the fallback memory too (for testing)
            self.fallback_memory.append({"role": role, "content": content})
        else:
            # Simple list-based memory 
            self.memory.append({"role": role, "content": content})
        
        logger.info(f"Added to memory ({role}): {content[:50]}...")
    
    def extract_appointment_details(self, message: str) -> Dict[str, Any]:
        """
        Extract appointment details from a message using LangChain and ChatBedrock.
        
        Args:
            message: The user message to extract details from
            
        Returns:
            A dictionary with extracted date, time, and purpose
        """
        try:
            logger.info(f"Extracting appointment details from: {message}")
            self.add_to_memory("user", message)
            
            if LANGCHAIN_AVAILABLE:
                # Use LangChain for extraction
                chain = self._create_extraction_chain()
                response = chain.invoke({"input": message})
                
                # Extract the text from the response
                response_text = response.get("text", "")
                logger.info(f"Raw extraction response: {response_text}")
                
                # Parse the JSON from the response
                extracted_details = json.loads(response_text)
                
                # Add the response to memory
                self.add_to_memory("assistant", json.dumps(extracted_details))
                
                return extracted_details
            else:
                # Fallback to basic implementation
                return self._basic_extraction(message)
                
        except Exception as e:
            logger.error(f"Error extracting appointment details: {str(e)}", exc_info=True)
            return {"date": None, "time": None, "purpose": None}
    
    def _basic_extraction(self, message: str) -> Dict[str, Any]:
        """Fallback method if LangChain is not available"""
        try:
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
            
            # Add the response to memory
            self.add_to_memory("assistant", json.dumps(extracted_details))
            
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
            
            return details
            
        except Exception as e:
            logger.error(f"Error in basic extraction: {str(e)}", exc_info=True)
            return {"date": None, "time": None, "purpose": None}
            
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        if LANGCHAIN_AVAILABLE:
            # In a real production environment, we would parse the LangChain memory
            # But for testing, we'll use our fallback memory
            return self.fallback_memory
        else:
            # Return the simple list-based memory
            return self.memory
