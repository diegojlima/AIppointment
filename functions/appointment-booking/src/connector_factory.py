
# functions/appointment-booking/src/connector_factory.py
import logging
from typing import Dict, Any, Type
from connector_registry import ConnectorInterface, ConnectorRegistry, HttpConnector, SlackConnector
from whatsapp_connector import WhatsAppConnector

logger = logging.getLogger(__name__)

# Mapping of connector types to classes
CONNECTOR_CLASSES = {
    "HTTP": HttpConnector,
    "SLACK": SlackConnector,
    "WHATSAPP": WhatsAppConnector,
    # Extend with additional types as needed.
}

def create_connector_registry(config_items: list) -> ConnectorRegistry:
    """
    Create a connector registry with the specified configuration items.
    
    Args:
        config_items: List of connector configuration items
        
    Returns:
        Initialized ConnectorRegistry
    """
    return ConnectorRegistry(config_items, CONNECTOR_CLASSES)
