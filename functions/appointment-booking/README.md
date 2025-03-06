# AIppointment - LangChain Integration

## Implementation Plan

This document outlines the implementation plan for Phase 1 of the AIppointment project roadmap.

### Phase 1: Foundation Improvements

1. ✅ Implement LangChain for better AI interactions
   - Created basic and enhanced LangChain agents for appointment extraction
   - Added conversation memory for context-aware responses
   - Used ChatBedrock integration for Claude 3 models

2. ⬜ Complete the WhatsApp Business API integration

3. ⬜ Enhance the state machine with more states and transitions

## Implementation Details

### LangChain Integration

We've implemented two versions of the LangChain agent:

1. **Basic Agent (`langchain_agent_basic.py`)**
   - Simple implementation using direct Bedrock API calls
   - Extracts appointment details from user messages
   - Fully tested with mocked responses

2. **Enhanced Agent (`langchain_agent_enhanced.py`)**
   - Uses LangChain's ChatBedrock for improved interactions
   - Maintains conversation memory for context-aware responses
   - Gracefully falls back to basic implementation if LangChain is not available
   - Fully tested with mocked LangChain components

### Key Components

- **ChatBedrock Integration**: Uses LangChain's ChatBedrock to interact with Claude 3 models
- **Conversation Memory**: Maintains context across multiple interactions
- **Extraction Chain**: Specialized chain for extracting appointment details
- **Error Handling**: Graceful fallbacks for missing dependencies

### Test Strategy

We've implemented a comprehensive test suite:

- Unit tests for both basic and enhanced implementations
- Mock components to avoid actual API calls
- Tests for memory and conversation history
- Tests for error handling and fallback mechanisms

### Files to Use

#### Implementation Files
- `langchain_agent_basic.py` - Basic agent using direct Bedrock API
- `langchain_agent_enhanced.py` - Enhanced agent using LangChain

#### Test Files
- `test_langchain_agent_basic.py` - Tests for the basic agent
- `test_langchain_agent_enhanced.py` - Tests for the enhanced agent

> Note: There are other files in the repository that were created during exploration and development. For a clean implementation, focus on the four files listed above.

### Next Steps

1. Install required LangChain dependencies:
   ```bash
   pip install langchain==0.1.11 langchain-aws==0.1.1 boto3>=1.34.72
   ```

2. Integrate the LangChain agent with the main application flow:
   ```python
   # Example integration
   from langchain_agent_enhanced import LangChainAgentEnhanced
   
   # In your Lambda handler
   def process_message(message, session_id=None):
       # Initialize the LangChain agent
       agent = LangChainAgentEnhanced(session_id=session_id)
       
       # Extract appointment details
       appointment_details = agent.extract_appointment_details(message)
       
       # Handle missing information if needed
       if appointment_details.get("date") is None or appointment_details.get("time") is None:
           appointment_details = agent.fetch_missing_information(appointment_details, message)
           
       return appointment_details
   ```

3. Implement the WhatsApp Business API integration

4. Enhance the state machine with improved conversation states

## Usage Example

```python
from langchain_agent_enhanced import LangChainAgentEnhanced

# Initialize the agent
agent = LangChainAgentEnhanced(session_id="user-123")

# Extract appointment details
result = agent.extract_appointment_details("I need a dental checkup next Wednesday at 2pm")
print(result)
# {'date': '2023-09-20', 'time': '14:00', 'purpose': 'dental checkup'}

# The agent maintains conversation memory
agent.get_conversation_history()
# [{'role': 'user', 'content': 'I need a dental checkup next Wednesday at 2pm'},
#  {'role': 'assistant', 'content': '{"date": "2023-09-20", "time": "14:00", "purpose": "dental checkup"}'}]
```
