# functions/appointment-booking/tests/test_langchain_agent_basic.py
import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

class TestLangChainAgentBasic:
    
    def test_agent_initialization(self):
        """Test if the LangChainAgent initializes properly"""
        # Import the module
        from langchain_agent_basic import LangChainAgentBasic
        
        # Create an instance of the agent
        agent = LangChainAgentBasic()
        
        # Basic assertions to check it was initialized correctly
        assert agent is not None
        assert hasattr(agent, 'extract_appointment_details')
    
    def test_extract_appointment_with_mocked_bedrock(self):
        """Test appointment extraction with a mocked Bedrock client"""
        from langchain_agent_basic import LangChainAgentBasic
        
        # Create a mock Bedrock client
        mock_bedrock = MagicMock()
        
        # Mock the client's invoke_model method response
        mock_response = {
            'body': MagicMock(),
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [
                {
                    'type': 'text',
                    'text': json.dumps({
                        'date': '2023-09-20',
                        'time': '14:00',
                        'purpose': 'dental checkup'
                    })
                }
            ]
        }).encode('utf-8')
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Initialize the agent with our mock
        agent = LangChainAgentBasic(bedrock_client=mock_bedrock)
        
        # Call the extract method
        message = "I need a dental checkup next Wednesday at 2pm"
        result = agent.extract_appointment_details(message)
        
        # Verify the bedrock client was called
        mock_bedrock.invoke_model.assert_called_once()
        
        # Verify the result
        assert result is not None
        assert result['date'] == '2023-09-20'
        assert result['time'] == '14:00'
        assert result['purpose'] == 'dental checkup'
