# functions/appointment-booking/src/router.py
import logging
import json

logger = logging.getLogger(__name__)

def classify_intent(normalized_input):
    """
    Dummy intent classifier using keyword matching.
    In production, replace with an LLM-based classifier (e.g., AWS Bedrock Agents).
    Returns an intent string.
    """
    message = normalized_input.get("message", "").lower()
    if "agenda" in message:
        return "read_agenda"
    elif "book" in message and "appointment" in message:
        return "book_appointment"
    elif "send message" in message:
        return "send_message"
    elif "email" in message:
        return "fetch_emails"
    elif "whatsapp" in message and "read" in message:
        return "read_whatsapp"
    elif "health" in message:
        return "fetch_health_data"
    elif "post" in message and "instagram" in message:
        return "instagram_post"
    elif "save document" in message or "brainstorm" in message:
        return "save_document"
    else:
        return "unknown"

def route_request(normalized_input):
    """
    Routes the request to the appropriate handler based on the classified intent.
    Returns a tuple of (intent, payload) where payload includes the original message and any metadata.
    """
    intent = classify_intent(normalized_input)
    payload = {
        "phone_number": normalized_input.get("phone_number"),
        "message": normalized_input.get("message"),
        "session_id": normalized_input.get("session_id"),
        "channel": normalized_input.get("channel"),
    }
    logger.info(f"Classified intent: {intent} for payload: {json.dumps(payload)}")
    return intent, payload
