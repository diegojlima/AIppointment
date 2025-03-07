"""
End-to-end tests for AWS Bedrock Agent integration.

These tests require AWS credentials with the appropriate permissions to be set up in the environment.
They integrate with real AWS services and will incur costs.

To run these tests only when specifically requested, run with:
pytest -xvs tests/test_e2e_bedrock_agent.py
"""
import os
import json
import uuid
import pytest
import boto3
from datetime import datetime, timedelta

# Skip these tests if integration tests are not explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("ENABLE_INTEGRATION_TESTS") != "true",
    reason="Integration tests not enabled. Set ENABLE_INTEGRATION_TESTS=true to run."
)

@pytest.fixture
def bedrock_agent_runtime():
    """Create a boto3 client for Bedrock Agent Runtime."""
    return boto3.client('bedrock-agent-runtime')

@pytest.fixture
def unique_session_id():
    """Generate a unique session ID for the test."""
    return f"test-session-{uuid.uuid4()}"

@pytest.fixture
def agent_ids():
    """Get the agent ID and alias ID from environment variables or use default values."""
    agent_id = os.environ.get('BEDROCK_AGENT_ID')
    agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
    
    if not agent_id or not agent_alias_id:
        pytest.skip("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set in environment variables")
    
    return {
        'agent_id': agent_id,
        'agent_alias_id': agent_alias_id
    }

def test_agent_responds_to_greeting(bedrock_agent_runtime, unique_session_id, agent_ids):
    """Test that the agent responds appropriately to a greeting."""
    # Arrange
    input_text = "Hello, I need help with scheduling an appointment"
    
    # Act
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=unique_session_id,
        inputText=input_text
    )
    
    # Assert
    assert 'completion' in response
    assert len(response['completion']) > 0
    assert 'appointment' in response['completion'].lower()

def test_agent_extracts_appointment_details(bedrock_agent_runtime, unique_session_id, agent_ids):
    """Test that the agent correctly extracts appointment details."""
    # Arrange
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    input_text = f"I need an appointment tomorrow at 2pm for a consultation"
    
    # Act
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=unique_session_id,
        inputText=input_text
    )
    
    # Assert
    assert 'completion' in response
    assert len(response['completion']) > 0
    assert '2' in response['completion']
    assert 'pm' in response['completion'].lower()
    assert 'consultation' in response['completion'].lower()

def test_agent_check_availability(bedrock_agent_runtime, unique_session_id, agent_ids):
    """Test that the agent can check availability for a specific date."""
    # Arrange
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    input_text = f"What are the available slots on {next_week}?"
    
    # Act
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=unique_session_id,
        inputText=input_text
    )
    
    # Assert
    assert 'completion' in response
    assert len(response['completion']) > 0
    assert 'available' in response['completion'].lower()
    
    # The response should have at least one time slot
    found_time_pattern = any(t in response['completion'].lower() for t in ['am', 'pm', ':'])
    assert found_time_pattern

def test_full_appointment_booking_flow(bedrock_agent_runtime, agent_ids):
    """Test the full appointment booking flow from availability check to confirmation."""
    # Create a unique session ID for this test
    session_id = f"test-flow-{uuid.uuid4()}"
    
    # Step 1: Ask about availability
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    step1_response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=session_id,
        inputText=f"What slots are available on {next_week}?"
    )
    
    assert 'completion' in step1_response
    assert len(step1_response['completion']) > 0
    
    # Step 2: Book an appointment at 10am
    step2_response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=session_id,
        inputText=f"I'd like to book an appointment on {next_week} at 10am for a consultation"
    )
    
    assert 'completion' in step2_response
    assert len(step2_response['completion']) > 0
    assert '10' in step2_response['completion']
    assert 'confirm' in step2_response['completion'].lower() or 'book' in step2_response['completion'].lower()
    
    # Step 3: Confirm the appointment
    step3_response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_ids['agent_id'],
        agentAliasId=agent_ids['agent_alias_id'],
        sessionId=session_id,
        inputText="Yes, please confirm the appointment"
    )
    
    assert 'completion' in step3_response
    assert len(step3_response['completion']) > 0
    assert 'confirm' in step3_response['completion'].lower() or 'book' in step3_response['completion'].lower()
    assert '10' in step3_response['completion']
    assert next_week.replace('-', '/') in step3_response['completion'] or next_week in step3_response['completion']
