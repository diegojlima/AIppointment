# functions/appointment-booking/src/state_machine.py
import logging
from datetime import datetime
from agent_tools import fetch_missing_information  # Import the new tool function

logger = logging.getLogger(__name__)

class AssistantStateMachine:
    def __init__(self, session_id, memory_store=None):
        """
        Initialize the state machine with a session identifier and an optional memory store.
        For demonstration, memory_store is a simple dictionary.
        """
        self.session_id = session_id
        self.memory = memory_store if memory_store is not None else {}
        self.state = "INIT"
        self.context = {}

    def update_memory(self, key, value):
        """Update the session memory."""
        self.memory[key] = value
        logger.info(f"[Session {self.session_id}] Memory updated: {key} = {value}")

    def get_memory(self, key):
        """Retrieve a value from the session memory."""
        return self.memory.get(key)

    def transition(self, new_state):
        """Transition to a new state and log the change."""
        logger.info(f"[Session {self.session_id}] Transitioning from {self.state} to {new_state}")
        self.state = new_state

    def process_input(self, message, extracted_details):
        """
        Process the input message and extracted details through a generic conversation flow.
        Returns a response string representing the current step outcome.
        The flow now includes a TOOL_INVOCATION state to fetch missing information.
        """
        if self.state == "INIT":
            self.transition("EXTRACT_DETAILS")
            self.context['raw_message'] = message
            self.context['extracted'] = extracted_details
            self.update_memory("last_interaction", datetime.utcnow().isoformat())
            return "Details extracted. Moving to the next step."

        elif self.state == "EXTRACT_DETAILS":
            # Check for required keys; if missing, transition to TOOL_INVOCATION.
            if not extracted_details.get("date") or not extracted_details.get("time"):
                self.transition("TOOL_INVOCATION")
                # Invoke external tool (agent_tools) to fetch missing data.
                missing = fetch_missing_information(extracted_details)
                # Merge the fetched missing information.
                self.context['extracted'].update(missing)
                return f"Missing information obtained: {missing}. Moving to validation."
            else:
                self.transition("VALIDATE")
                return "All necessary details present. Proceeding to validation."

        elif self.state == "TOOL_INVOCATION":
            # After fetching missing details, assume we have updated context.
            if self.context['extracted'].get("date") and self.context['extracted'].get("time"):
                self.transition("VALIDATE")
                return "Missing details acquired. Proceeding to validation."
            else:
                return "Still missing essential details; cannot proceed."

        elif self.state == "VALIDATE":
            # In a real scenario, implement complex validation here.
            self.transition("CONFIRM")
            return "Details validated. Awaiting confirmation."

        elif self.state == "CONFIRM":
            self.transition("EXECUTE")
            return "Confirmation received. Executing requested operation."

        elif self.state == "EXECUTE":
            self.update_memory("action_status", "completed")
            return "Operation executed successfully."

        else:
            return "Encountered an undefined state."

# For local testing of the state machine
if __name__ == "__main__":
    sm = AssistantStateMachine(session_id="TEST123")
    # Simulate missing time to trigger tool invocation
    print(sm.process_input("I need assistance", {"date": "2023-09-18", "purpose": "checkup"}))
    # Now simulate that the missing information was fetched and validation can proceed
    print(sm.process_input("I need assistance", {"date": "2023-09-18", "time": "14:00", "purpose": "checkup"}))
