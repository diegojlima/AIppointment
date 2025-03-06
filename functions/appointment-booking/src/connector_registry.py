# functions/appointment-booking/src/connector_registry.py
import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Base interface for connectors
class ConnectorInterface(ABC):
    @abstractmethod
    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        """Execute a given action with provided parameters."""
        pass

    @classmethod
    @abstractmethod
    def get_full_instance_mapping_path(cls, metadata: Dict[str, Any]) -> str:
        """Return a unique key for an instance given its metadata."""
        pass

    @classmethod
    @abstractmethod
    def validate_connector_metadata(cls, metadata: Dict[str, Any]) -> None:
        """Validate that the metadata meets requirements for this connector."""
        pass

# Example HTTP connector
class HttpConnector(ConnectorInterface):
    def __init__(self, metadata: Dict[str, Any], connection_params: Dict[str, Any]):
        self.metadata = metadata
        self.connection_params = connection_params

    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        logger.info(f"[HTTP] Executing action '{action_name}' with params {params}")
        # Here you could perform an actual HTTP request.
        return f"[HTTP] Action '{action_name}' executed."

    @classmethod
    def get_full_instance_mapping_path(cls, metadata: Dict[str, Any]) -> str:
        return f"http_{metadata.get('id', 'default')}"

    @classmethod
    def validate_connector_metadata(cls, metadata: Dict[str, Any]) -> None:
        if 'id' not in metadata:
            raise ValueError("HTTP connector metadata must include 'id'.")

# Example Slack connector
class SlackConnector(ConnectorInterface):
    def __init__(self, metadata: Dict[str, Any], connection_params: Dict[str, Any]):
        self.metadata = metadata
        self.connection_params = connection_params

    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        logger.info(f"[Slack] Executing action '{action_name}' with params {params}")
        # Simulate sending a message via Slack API.
        return f"[Slack] Action '{action_name}' executed."

    @classmethod
    def get_full_instance_mapping_path(cls, metadata: Dict[str, Any]) -> str:
        return f"slack_{metadata.get('channel', 'default')}"

    @classmethod
    def validate_connector_metadata(cls, metadata: Dict[str, Any]) -> None:
        if 'channel' not in metadata:
            raise ValueError("Slack connector metadata must include 'channel'.")

# Mapping of connector types to classes
CONNECTOR_CLASSES = {
    "HTTP": HttpConnector,
    "SLACK": SlackConnector,
    # Extend with additional types as needed.
}

class ConnectorRegistry:
    def __init__(self, config_items: list):
        """
        Initialize connector instances based on a configuration list.
        Each item in config_items is a dict with keys:
          - connectorType (e.g., "HTTP", "SLACK")
          - connectorMetadata (dict)
          - connectorConnectionParams (dict)
        """
        self.connector_instances: Dict[str, ConnectorInterface] = {}
        for config_item in config_items:
            connector_type = config_item.get("connectorType")
            metadata = config_item.get("connectorMetadata")
            connection_params = config_item.get("connectorConnectionParams")
            connector_class = CONNECTOR_CLASSES.get(connector_type)
            if not connector_class:
                raise ValueError(f"Invalid connector type: {connector_type}")
            connector_class.validate_connector_metadata(metadata)
            key = connector_class.get_full_instance_mapping_path(metadata)
            instance = connector_class(metadata, connection_params)
            self.connector_instances[key] = instance
            logger.info(f"Initialized connector instance with key: {key}")

    def get_connector_instance(self, connector_type: str, metadata: Dict[str, Any]) -> ConnectorInterface:
        connector_class = CONNECTOR_CLASSES.get(connector_type)
        if not connector_class:
            raise ValueError(f"Invalid connector type: {connector_type}")
        key = connector_class.get_full_instance_mapping_path(metadata)
        instance = self.connector_instances.get(key)
        if not instance:
            raise ValueError(f"Connector instance not found for key: {key}")
        return instance

    def execute_action(self, connector_type: str, metadata: Dict[str, Any], action_name: str, params: Dict[str, Any]) -> Any:
        instance = self.get_connector_instance(connector_type, metadata)
        return instance.execute_action(action_name, params)

# For local testing:
if __name__ == "__main__":
    config_items = [
        {"connectorType": "HTTP", "connectorMetadata": {"id": "123"}, "connectorConnectionParams": {}},
        {"connectorType": "SLACK", "connectorMetadata": {"channel": "general"}, "connectorConnectionParams": {}},
    ]
    registry = ConnectorRegistry(config_items)
    result_http = registry.execute_action("HTTP", {"id": "123"}, "fetch_data", {"url": "https://example.com"})
    result_slack = registry.execute_action("SLACK", {"channel": "general"}, "send_message", {"text": "Hello, world!"})
    print(result_http)
    print(result_slack)
