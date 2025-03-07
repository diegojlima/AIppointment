import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.state_machine import AssistantStateMachine

class TestAssistantStateMachine:
    """
    Test suite for the enhanced AssistantStateMachine.
    Tests the basic functionality and various state transitions.
    """
    
    # Tests for current functionality
    # (Keeping existing tests)
    
    def test_initialization(self):
        """Test state machine initialization with default and custom values."""
        # Test with default values
        sm = AssistantStateMachine(session_id="test123")
        assert sm.session_id == "test123"
        assert sm.state == "INIT"
        assert sm.memory == {}
        assert sm.context == {}
        
        # Test with custom memory store
        custom_memory = {"key": "value"}
        sm_with_memory = AssistantStateMachine(session_id="test456", memory_store=custom_memory)
        assert sm_with_memory.memory == custom_memory
    
    def test_memory_operations(self):
        """Test memory manipulation operations."""
        sm = AssistantStateMachine(session_id="test123")
        
        # Test update_memory
        sm.update_memory("test_key", "test_value")
        assert sm.memory.get("test_key") == "test_value"
        
        # Test get_memory
        assert sm.get_memory("test_key") == "test_value"
        assert sm.get_memory("non_existent_key") is None
    
    def test_state_transition(self):
        """Test state transitions."""
        sm = AssistantStateMachine(session_id="test123")
        assert sm.state == "INIT"
        
        sm.transition("NEW_STATE")
        assert sm.state == "NEW_STATE"
    
    def test_basic_flow(self):
        """Test the basic conversation flow with complete information."""
        sm = AssistantStateMachine(session_id="test123")
        
        # Initial state
        assert sm.state == "INIT"
        
        # First message with complete information
        response = sm.process_input(
            "I need an appointment tomorrow at 2pm",
            {"date": "2023-09-18", "time": "14:00", "purpose": "checkup"}
        )
        
        # Should transition to EXTRACT_DETAILS and then straight to VALIDATE
        assert "Details extracted" in response
        assert sm.state == "EXTRACT_DETAILS"
        
        # Process again to move to VALIDATE
        response = sm.process_input(
            "I need an appointment tomorrow at 2pm",
            {"date": "2023-09-18", "time": "14:00", "purpose": "checkup"}
        )
        
        assert "All necessary details present" in response
        assert sm.state == "VALIDATE"
    
    # Tests for new enhanced functionality
    def test_disambiguation_flow(self):
        """
        Test the flow when the user provides ambiguous information that needs clarification.
        For example, if a date is mentioned without specifying if it's for morning or afternoon.
        """
        sm = AssistantStateMachine(session_id="test123")
        
        # Initial state
        assert sm.state == "INIT"
        
        # First message with ambiguous information
        response = sm.process_input(
            "I need an appointment on Friday",
            {"date": "2023-09-22", "time": "afternoon", "purpose": "checkup"}
        )
        
        # Should transition to EXTRACT_DETAILS
        assert sm.state == "EXTRACT_DETAILS"
        
        # Process again, but with ambiguous time
        response = sm.process_input(
            "I need an appointment on Friday afternoon",
            {"date": "2023-09-22", "time": "afternoon", "purpose": "checkup"}
        )
        
        # Should transition to DISAMBIGUATION
        assert "need to clarify" in response.lower() or "please specify" in response.lower()
        assert sm.state == "DISAMBIGUATION"
        
        # Provide more specific time
        response = sm.process_input(
            "3pm would be good",
            {"date": "2023-09-22", "time": "15:00", "purpose": "checkup"}
        )
        
        # Should now move to VALIDATE with the clarified information
        assert "clarification" in response.lower() or "proceeding" in response.lower()
        assert sm.state == "VALIDATE"
    
    def test_conflict_resolution_flow(self):
        """
        Test the flow when there's a scheduling conflict that needs resolution.
        For example, when the requested time is already booked.
        """
        sm = AssistantStateMachine(session_id="test123")
        sm.transition("VALIDATE")
        
        # Simulate a conflict during validation
        sm.update_memory("conflicts", [
            {"date": "2023-09-18", "time": "14:00"},
            {"date": "2023-09-18", "time": "15:00"},
        ])
        
        # Process the validation with conflict
        response = sm.process_input(
            "I want an appointment on Monday at 2pm",
            {"date": "2023-09-18", "time": "14:00", "purpose": "checkup"}
        )
        
        # Should transition to CONFLICT_RESOLUTION
        assert "conflict" in response.lower() or "already booked" in response.lower()
        assert sm.state == "CONFLICT_RESOLUTION"
        
        # Suggest alternative and get user preference
        response = sm.process_input(
            "I can do 4pm instead",
            {"date": "2023-09-18", "time": "16:00", "purpose": "checkup"}
        )
        
        # Should accept the alternative and proceed to CONFIRM
        assert "available" in response.lower() or "can schedule" in response.lower()
        assert sm.state == "CONFIRM"
    
    def test_cancellation_flow(self):
        """
        Test the flow when the user wants to cancel the current booking process.
        """
        sm = AssistantStateMachine(session_id="test123")
        sm.transition("EXTRACT_DETAILS")
        
        # User decides to cancel
        response = sm.process_input(
            "Actually, I want to cancel this booking",
            {"intent": "cancel"}
        )
        
        # Should transition to CANCELLATION
        assert "cancel" in response.lower() or "stopping" in response.lower()
        assert sm.state == "CANCELLATION"
        
        # Confirm cancellation
        response = sm.process_input(
            "Yes, please cancel",
            {"intent": "confirm_cancel"}
        )
        
        # Should finalize cancellation and reset or end
        assert "cancelled" in response.lower() or "ended" in response.lower()
        assert sm.state == "INIT" or sm.state == "END"
    
    def test_reschedule_existing_flow(self):
        """
        Test the flow when the user wants to reschedule an existing appointment.
        """
        sm = AssistantStateMachine(session_id="test123")
        
        # Setup an existing appointment in memory
        sm.update_memory("existing_appointments", [
            {"id": "appt123", "date": "2023-09-20", "time": "10:00", "purpose": "checkup"}
        ])
        
        # User wants to reschedule
        response = sm.process_input(
            "I need to reschedule my appointment on Wednesday",
            {"intent": "reschedule", "date": "2023-09-20"}
        )
        
        # Should transition to IDENTIFY_APPOINTMENT
        assert "which appointment" in response.lower() or "found your appointment" in response.lower()
        assert sm.state == "IDENTIFY_APPOINTMENT"
        
        # Confirm the appointment to reschedule
        response = sm.process_input(
            "Yes, that one at 10am",
            {"appointment_id": "appt123"}
        )
        
        # Should transition to RESCHEDULE
        assert "when would you like" in response.lower() or "new time" in response.lower()
        assert sm.state == "RESCHEDULE"
        
        # Provide new time
        response = sm.process_input(
            "Friday at 2pm",
            {"date": "2023-09-22", "time": "14:00"}
        )
        
        # Should validate the new time
        assert sm.state == "VALIDATE" or sm.state == "CONFIRM_RESCHEDULE"
    
    def test_follow_up_flow(self):
        """
        Test the flow for appointment follow-ups, like reminders or post-appointment actions.
        """
        sm = AssistantStateMachine(session_id="test123")
        
        # Setup an upcoming appointment in memory
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        sm.update_memory("upcoming_appointments", [
            {"id": "appt456", "date": tomorrow, "time": "11:00", "purpose": "checkup"}
        ])
        
        # User asks about upcoming appointments
        response = sm.process_input(
            "Do I have any appointments coming up?",
            {"intent": "check_schedule"}
        )
        
        # Should transition to APPOINTMENT_LOOKUP
        assert "yes" in response.lower() and "tomorrow" in response.lower()
        assert sm.state == "APPOINTMENT_LOOKUP"
        
        # Ask for a reminder
        response = sm.process_input(
            "Can you send me a reminder?",
            {"intent": "request_reminder", "appointment_id": "appt456"}
        )
        
        # Should set up a reminder
        assert "remind" in response.lower() or "notification" in response.lower()
        assert sm.state == "REMINDER_SETUP"
        
        # Respond to the reminder prompt
        response = sm.process_input(
            "Yes, that's perfect",
            {"reminder_time": "1 hour before"}
        )
        
        # Should confirm the reminder setup
        assert "set up" in response.lower() or "reminder" in response.lower()
        assert sm.state == "END"
        
        # Request something else
        response = sm.process_input(
            "I need something else",
            {"intent": "new_request"}
        )
        
        assert "help" in response.lower()
        assert sm.state == "END"
        
        # Final response
        response = sm.process_input(
            "Thanks",
            {"intent": "thank_you"}
        )
        
        assert "help" in response.lower() or "welcome" in response.lower()
        assert sm.state == "END"
    
    def test_missing_information_flow(self):
        """Test the flow when information is missing and needs to be fetched."""
        sm = AssistantStateMachine(session_id="test123")
        
        # Initial state
        assert sm.state == "INIT"
        
        # First message with incomplete information (missing time)
        response = sm.process_input(
            "I need an appointment tomorrow",
            {"date": "2023-09-18", "purpose": "checkup"}
        )
        
        # Should transition to EXTRACT_DETAILS
        assert sm.state == "EXTRACT_DETAILS"
        
        # Process again to try to move to VALIDATE, but should go to TOOL_INVOCATION
        response = sm.process_input(
            "I need an appointment tomorrow",
            {"date": "2023-09-18", "purpose": "checkup"}
        )
        
        assert "Missing information obtained" in response
        assert sm.state == "TOOL_INVOCATION"
        
        # After tool invocation, should have all information and move to VALIDATE
        response = sm.process_input(
            "What time works?",
            {"date": "2023-09-18", "time": "09:00", "purpose": "checkup"}
        )
        
        assert "Missing details acquired" in response
        assert sm.state == "VALIDATE"
