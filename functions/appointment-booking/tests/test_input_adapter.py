import pytest
import json

# Add the path to the src directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module to test
from input_adapter import normalize_input

def test_normalize_input_valid_json():
    # Test with valid JSON body
    event = {
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'I need an appointment',
            'channel': 'whatsapp',
            'session_id': 'session-123'
        })
    }
    
    result = normalize_input(event)
    
    assert result['phone_number'] == '+1234567890'
    assert result['message'] == 'I need an appointment'
    assert result['channel'] == 'whatsapp'
    assert result['session_id'] == 'session-123'

def test_normalize_input_invalid_json():
    # Test with invalid JSON body
    event = {
        'body': 'not-json'
    }
    
    result = normalize_input(event)
    
    assert result['phone_number'] is None
    assert result['message'] is None
    assert result['channel'] == 'unknown'
    assert result['session_id'] is None

def test_normalize_input_missing_fields():
    # Test with missing fields
    event = {
        'body': json.dumps({
            'message': 'I need an appointment'
            # Missing phone_number, channel, session_id
        })
    }
    
    result = normalize_input(event)
    
    assert result['phone_number'] is None
    assert result['message'] == 'I need an appointment'
    assert result['channel'] == 'unknown'
    assert result['session_id'] is None

def test_normalize_input_empty_body():
    # Test with empty body
    event = {}
    
    result = normalize_input(event)
    
    assert result['phone_number'] is None
    assert result['message'] is None
    assert result['channel'] == 'unknown'
    assert result['session_id'] is None
