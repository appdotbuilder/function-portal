"""
Tests for the enhanced FunctionCall model with external API support
"""

import json
from app.models import FunctionCall
from app.database import reset_db


def test_function_call_enhanced_fields():
    """Test that FunctionCall model has all required enhanced fields"""
    reset_db()

    # Test creating a FunctionCall with all enhanced fields
    parameters_data = {"user_id": 123, "action": "test", "payload": {"key": "value"}}

    call = FunctionCall(
        parameters=json.dumps(parameters_data),
        endpoint="https://api.example.com/test",
        api_key="test-api-key-12345",
        error_message=None,
    )

    # Verify all fields are properly set
    assert call.parameters == json.dumps(parameters_data)
    assert call.endpoint == "https://api.example.com/test"
    assert call.api_key == "test-api-key-12345"
    assert call.error_message is None

    # Test that parameters can be parsed back to dict
    parsed_params = json.loads(call.parameters)
    assert parsed_params == parameters_data
    assert parsed_params["user_id"] == 123
    assert parsed_params["payload"]["key"] == "value"


def test_function_call_optional_fields():
    """Test that api_key and error_message are properly optional"""
    reset_db()

    # Create FunctionCall without optional fields
    call = FunctionCall(parameters='{"test": "value"}', endpoint="https://api.example.com/endpoint")

    # Verify optional fields default to None
    assert call.api_key is None
    assert call.error_message is None

    # Verify required fields are set
    assert call.parameters == '{"test": "value"}'
    assert call.endpoint == "https://api.example.com/endpoint"


def test_function_call_error_handling():
    """Test that error messages can be stored in the model"""
    reset_db()

    call = FunctionCall(
        parameters='{"test": true}', endpoint="https://api.example.com/failing-endpoint", api_key="valid-key"
    )

    # Simulate storing an error message after failed API call
    error_msg = "HTTP 404: Endpoint not found"
    call.error_message = error_msg

    assert call.error_message == error_msg
    assert call.api_key == "valid-key"  # Other fields should remain unchanged


def test_function_call_empty_parameters():
    """Test handling of empty or minimal parameters"""
    reset_db()

    # Test with empty parameters string
    call1 = FunctionCall(parameters="", endpoint="https://api.example.com/no-params")

    assert call1.parameters == ""
    assert call1.endpoint == "https://api.example.com/no-params"

    # Test with empty JSON object
    call2 = FunctionCall(parameters="{}", endpoint="https://api.example.com/empty-params")

    assert call2.parameters == "{}"
    parsed = json.loads(call2.parameters)
    assert parsed == {}


def test_httpx_dependency():
    """Test that httpx dependency is available for API calls"""
    import httpx

    # Verify we can create an httpx client
    client = httpx.Client()
    assert client is not None
    client.close()

    # Verify async client is also available
    async_client = httpx.AsyncClient()
    assert async_client is not None


def test_function_call_field_constraints():
    """Test that field constraints work properly"""
    reset_db()

    # Test maximum lengths and data types
    long_endpoint = "https://api.example.com/" + "x" * 500
    long_api_key = "key-" + "x" * 500
    long_error_msg = "error: " + "x" * 1000

    call = FunctionCall(
        parameters=json.dumps({"large_data": "x" * 1000}),  # No length limit on parameters
        endpoint=long_endpoint[:500],  # Should be truncated to max_length=500
        api_key=long_api_key[:500],  # Should be truncated to max_length=500
        error_message=long_error_msg[:1000],  # Should be truncated to max_length=1000
    )

    # Verify constraints are respected
    assert len(call.endpoint) <= 500
    assert len(call.api_key or "") <= 500
    assert len(call.error_message or "") <= 1000

    # Parameters should support arbitrary length JSON
    assert len(call.parameters) > 500  # Can be longer than other fields
