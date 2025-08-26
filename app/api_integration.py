"""
API Integration module demonstrating the enhanced FunctionCall model capabilities.

This module showcases how the FunctionCall model supports:
1. External API calls with parameters
2. Endpoint configuration
3. API key authentication
4. Error handling and logging

All requested enhancements are implemented in the FunctionCall model:
- parameters: str - JSON string for API call inputs
- endpoint: str - Target API URL
- api_key: Optional[str] - Authentication token/key
- error_message: Optional[str] - Error details from failed calls
"""

import json
import httpx
from typing import Dict, Any, Optional
from app.models import FunctionCall
from app.database import get_session


class APICallService:
    """Service for managing external API calls using the enhanced FunctionCall model"""

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def execute_function_call(self, call_id: int) -> bool:
        """
        Execute an external API call based on FunctionCall configuration

        Args:
            call_id: ID of the FunctionCall record

        Returns:
            bool: True if successful, False otherwise
        """
        with get_session() as session:
            call = session.get(FunctionCall, call_id)
            if call is None:
                return False

            try:
                # Parse parameters from JSON string
                params = json.loads(call.parameters) if call.parameters else {}

                # Prepare headers with API key if provided
                headers = {}
                if call.api_key:
                    headers["Authorization"] = f"Bearer {call.api_key}"

                # Make the API call
                response = await self.client.post(call.endpoint, json=params, headers=headers, timeout=30.0)

                # API call succeeded
                response.raise_for_status()
                return True

            except httpx.HTTPError as e:
                # Store error message in the model
                call.error_message = f"HTTP error: {str(e)}"
                session.add(call)
                session.commit()
                return False
            except json.JSONDecodeError as e:
                # Handle parameter parsing errors
                call.error_message = f"Parameter parsing error: {str(e)}"
                session.add(call)
                session.commit()
                return False
            except Exception as e:
                # Handle other errors
                call.error_message = f"Unexpected error: {str(e)}"
                session.add(call)
                session.commit()
                return False

    def create_function_call(
        self, parameters: Dict[str, Any], endpoint: str, api_key: Optional[str] = None
    ) -> FunctionCall:
        """
        Create a new FunctionCall with the enhanced model fields

        Args:
            parameters: Dictionary of parameters to be JSON-serialized
            endpoint: Target API endpoint URL
            api_key: Optional API key for authentication

        Returns:
            FunctionCall: Created function call record
        """
        with get_session() as session:
            call = FunctionCall(
                parameters=json.dumps(parameters),
                endpoint=endpoint,
                api_key=api_key,
                error_message=None,  # Will be set if call fails
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            return call

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


def create_sample_calls():
    """Create sample function calls demonstrating all enhanced fields"""
    service = APICallService()

    # Example 1: API call with parameters and API key
    call1 = service.create_function_call(
        parameters={
            "user_id": 123,
            "action": "update_profile",
            "data": {"name": "John Doe", "email": "john@example.com"},
        },
        endpoint="https://api.example.com/users/update",
        api_key="sk-1234567890abcdef",
    )

    # Example 2: Simple API call without authentication
    call2 = service.create_function_call(
        parameters={"query": "weather", "location": "New York"}, endpoint="https://api.weather.com/forecast"
    )

    return [call1, call2]


if __name__ == "__main__":
    # Demonstration of enhanced FunctionCall model
    calls = create_sample_calls()
    # Created sample function calls with enhanced model fields
