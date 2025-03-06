# functions/appointment-booking/tests/test_langchain_agent_enhanced.py
import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Create a simple mock for LangChain's ChatBedrock
class MockChatBedrock:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def invoke(self, input_text):
        # Return a fixed response for testing
        return {"text": json.dumps({
            "date": "2023-09-20",
            "time": "14:00",
            "purpose": "dental checkup"
        })}

# Create a mock for LangChain's LLMChain
class MockLLMChain:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def invoke(self, inputs):
        # Return a fixed response for testing
        return {"text": json.dumps({
            "date": "2023-09-20",
            "time": "14:00",
            "purpose": "dental checkup"
        })}

# Patch the LangChain imports
@pytest.fixture(autouse=True)
def mock_langchain_imports():
    with patch.dict('sys.modules', {
        'langchain_aws': MagicMock(),
        'langchain.prompts': MagicMock(),
        'langchain.schema': MagicMock(),
        'langchain.chains': MagicMock(),
        'langchain.memory': MagicMock()
    }):
        # Patch specific classes we're using
        sys.modules['langchain_aws'].ChatBedrock = MockChatBedrock
        sys.modules['langchain.chains'].LLMChain = MockLLMChain
        sys.modules['langchain.memory'].ConversationBufferMemory = MagicMock
        yield

class TestLangChainAgentEnhanced:
    
    def test_agent_initialization(self):
        """Test if the enhanced LangChain agent initializes properly"""
        from langchain_agent_enhanced import LangChainAgentEnhanced
        
        # Create an instance of the agent
        agent = LangChainAgentEnhanced()
        
        # Basic assertions to check it was initialized correctly
        assert agent is not None
        assert hasattr(agent, 'extract_appointment_details')
        assert hasattr(agent, 'add_to_memory')
        assert hasattr(agent, 'get_conversation_history')
    
    def test_extract_appointment_with_langchain(self):
        """Test appointment extraction with mocked LangChain components"""
        from langchain_agent_enhanced import LangChainAgentEnhanced, LANGCHAIN_AVAILABLE
        
        # Skip test if LangChain is not available
        if not LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain not available")
        
        # Create a mock Bedrock client
        mock_bedrock = MagicMock()
        
        # Initialize the agent with our mock
        agent = LangChainAgentEnhanced(bedrock_client=mock_bedrock)
        
        # Patch the _create_extraction_chain method to return our mock
        with patch.object(agent, '_create_extraction_chain', return_value=MockLLMChain()):
            # Call the extract method
            message = "I need a dental checkup next Wednesday at 2pm"
            result = agent.extract_appointment_details(message)
            
            # Verify the result
            assert result is not None
            assert result['date'] == '2023-09-20'
            assert result['time'] == '14:00'
            assert result['purpose'] == 'dental checkup'
    
    def test_conversation_memory(self):
        """Test that the agent properly maintains conversation memory"""
        from langchain_agent_enhanced import LangChainAgentEnhanced
        
        # Create an instance of the agent
        agent = LangChainAgentEnhanced()
        
        # Add some messages to memory
        agent.add_to_memory("user", "I need an appointment")
        agent.add_to_memory("assistant", "What time works for you?")
        
        # Ensure the messages were added to memory
        history = agent.get_conversation_history()
        
        # The implementation here will depend on whether LangChain is available or not
        # So we'll just check that we have something in the history
        assert history is not None
        
        # If using the fallback memory, we should have 2 items
        if not agent.memory.__class__.__name__ == 'ConversationBufferMemory':
            assert len(history) == 2
            assert history[0]['role'] == 'user'
            assert history[0]['content'] == 'I need an appointment'
