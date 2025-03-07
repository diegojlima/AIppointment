# AIppointment - LangChain Integration

## Implementation Plan

This document outlines the implementation plan for Phase 1 of the AIppointment project roadmap.

### Phase 1: Foundation Improvements

1. ✅ Implement LangChain for better AI interactions
   - Created basic and enhanced LangChain agents for appointment extraction
   - Added conversation memory for context-aware responses
   - Used ChatBedrock integration for Claude 3 models

2. ✅ Complete the WhatsApp Business API integration

3. ⬜ Enhance the state machine with more states and transitions

4. ⬜ Calendar system integration for availability checking

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

### WhatsApp Business API Integration

We've implemented a comprehensive WhatsApp Business API integration with the following components:

1. **WhatsApp Connector (`whatsapp_connector.py`)**
   - Integration with WhatsApp Cloud API for sending and receiving messages
   - Support for text messages and template messages
   - Webhook handling for incoming messages
   - Verification endpoint for webhook setup

2. **Multi-Channel Handler (`multi_channel.py`)**
   - Channel-agnostic messaging framework
   - Message normalization across different channels
   - Support for both incoming and outgoing messages
   - Extensible design for future channel integrations

3. **Connector Registry Update**
   - Added WhatsApp connector to the registry system
   - Standardized interface for accessing messaging channels

### Key Capabilities

- **Sending Text Messages**: Send plain text messages to WhatsApp users
- **Template Messages**: Send structured messages using approved WhatsApp templates
- **Incoming Message Processing**: Parse and normalize incoming WhatsApp messages
- **Webhook Verification**: Support for setting up and verifying WhatsApp webhooks
- **Configuration Management**: Flexible configuration for multiple WhatsApp numbers

### Test Strategy

We've implemented comprehensive tests for both the WhatsApp connector and multi-channel handler:

- Unit tests for the WhatsApp connector implementation
- Tests for webhook message processing
- Tests for sending text and template messages
- Tests for multi-channel message normalization

### Files to Use

#### Implementation Files
- `whatsapp_connector.py` - WhatsApp Business API connector
- `multi_channel.py` - Multi-channel messaging handler
- `config/whatsapp_config.json` - Configuration template for WhatsApp

#### Test Files
- `test_whatsapp_connector.py` - Tests for the WhatsApp connector
- `test_multi_channel.py` - Tests for the multi-channel handler

### Next Steps

1. Install required dependencies:
   ```bash
   pip install langchain==0.1.11 langchain-aws==0.1.1 boto3>=1.34.72 requests>=2.31.0
   ```

2. Set up a WhatsApp Business Account and obtain required credentials

3. Update the WhatsApp configuration file with your credentials:
   ```json
   // functions/appointment-booking/src/config/whatsapp_config.json
   [
     {
       "connectorType": "WHATSAPP",
       "connectorMetadata": {
         "phone_number_id": "YOUR_PHONE_NUMBER_ID",
         "business_account_id": "YOUR_BUSINESS_ACCOUNT_ID"
       },
       "connectorConnectionParams": {
         "access_token": "YOUR_ACCESS_TOKEN",
         "webhook_verify_token": "YOUR_VERIFY_TOKEN",
         "api_version": "v17.0"
       }
     }
   ]
   ```

4. Integrate the multi-channel handler with the LangChain agent:
   ```python
   # Example integration
   from langchain_agent_enhanced import LangChainAgentEnhanced
   from multi_channel import MultiChannelHandler
   
   # Initialize components
   agent = LangChainAgentEnhanced(session_id="user-123")
   multi_channel = MultiChannelHandler(config_file_path="config/whatsapp_config.json")
   
   # Process incoming message
   def process_whatsapp_message(webhook_payload):
       # Process the webhook
       result = multi_channel.process_incoming_message("WHATSAPP", webhook_payload)
       
       if not result.get("success", False):
           return {"error": result.get("error")}
       
       # Extract and process the first message
       if result.get("messages") and len(result["messages"]) > 0:
           message = result["messages"][0]
           
           # Extract appointment details using LangChain
           appointment_details = agent.extract_appointment_details(message["content"])
           
           # Send a response back to the user
           response = f"Appointment details extracted: Date: {appointment_details.get('date')}, Time: {appointment_details.get('time')}, Purpose: {appointment_details.get('purpose')}"
           
           # Get metadata from the original message
           metadata = {
               "phone_number_id": webhook_payload["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"],
               "business_account_id": webhook_payload["entry"][0]["id"]
           }
           
           # Send the response
           multi_channel.send_message(
               channel="WHATSAPP",
               recipient_id=message["sender_id"],
               message_type="text",
               content=response,
               metadata=metadata
           )
           
           return {"success": True, "appointment_details": appointment_details}
       
       return {"success": True, "message": "No messages to process"}
   ```

5. Enhance the state machine with improved conversation states

6. Implement calendar system integration for availability checking

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
