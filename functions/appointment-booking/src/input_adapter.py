# functions/appointment-booking/src/input_adapter.py
import json

def normalize_input(event):
    """
    Normalize incoming event from various channels (e.g., WhatsApp, Alexa, Google Home)
    into a standard dictionary with keys: phone_number, message, channel, session_id.
    
    Expected incoming event:
    {
      "body": "{\"phone_number\": \"+1234567890\", \"message\": \"I need an appointment at 2pm.\", \"channel\": \"whatsapp\", \"session_id\": \"ABC123\"}"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        body = {}
    
    normalized = {
        'phone_number': body.get('phone_number'),
        'message': body.get('message'),
        'channel': body.get('channel', 'unknown'),  # Default if not provided
        'session_id': body.get('session_id', None)     # Could be None if not supplied
    }
    return normalized
