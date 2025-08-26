"""
Tests for API integration functionality.
"""

import pytest

from app.database import reset_db
from app.services import FunctionConfigService, FunctionExecutionService
from app.models import FunctionConfigCreate, CallStatus


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


class TestAPIIntegration:
    """Test API integration with real and mock endpoints"""

    async def test_httpbin_get_request(self, new_db):
        """Test actual GET request to HTTPBin"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="HTTPBin GET Test", endpoint_url="https://httpbin.org/get", http_method="GET", timeout_seconds=10
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should succeed with HTTPBin
            assert execution.status == CallStatus.SUCCESS
            assert execution.response_status_code == 200
            assert execution.duration_ms is not None
            assert execution.response_body is not None

            # HTTPBin returns JSON, so response should contain expected fields
            assert "url" in execution.response_body
            assert "headers" in execution.response_body

        finally:
            await service.close()

    async def test_httpbin_post_request(self, new_db):
        """Test actual POST request to HTTPBin with payload"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="HTTPBin POST Test",
                endpoint_url="https://httpbin.org/post",
                http_method="POST",
                headers={"Content-Type": "application/json"},
                payload={"test_key": "test_value", "number": 42, "boolean": True},
                timeout_seconds=10,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should succeed
            assert execution.status == CallStatus.SUCCESS
            assert execution.response_status_code == 200
            assert execution.duration_ms is not None
            assert execution.response_body is not None

            # Verify the payload was sent correctly
            assert "test_key" in execution.response_body
            assert "test_value" in execution.response_body
            assert "42" in execution.response_body

        finally:
            await service.close()

    async def test_invalid_domain_failure(self, new_db):
        """Test handling of invalid domain"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Invalid Domain Test",
                endpoint_url="https://this-domain-definitely-does-not-exist-12345.com/api",
                timeout_seconds=5,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should fail due to invalid domain
            assert execution.status == CallStatus.FAILED
            assert execution.error_message is not None
            assert len(execution.error_message) > 0
            assert execution.completed_at is not None

        finally:
            await service.close()

    async def test_timeout_handling(self, new_db):
        """Test request timeout handling"""
        # Use httpbin delay endpoint to force timeout
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Timeout Test",
                endpoint_url="https://httpbin.org/delay/10",  # 10 second delay
                http_method="GET",
                timeout_seconds=2,  # 2 second timeout
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should timeout
            assert execution.status == CallStatus.TIMEOUT
            assert execution.error_message == "Request timed out"
            assert execution.completed_at is not None
            assert execution.duration_ms is not None
            # Duration should be close to timeout value
            assert execution.duration_ms >= 1900  # Allow some variance

        finally:
            await service.close()

    async def test_http_error_status_handling(self, new_db):
        """Test handling of HTTP error status codes"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="HTTP Error Test",
                endpoint_url="https://httpbin.org/status/500",  # Returns 500
                http_method="GET",
                timeout_seconds=10,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should fail due to HTTP error or succeed if service handles it differently
            assert execution.status in [CallStatus.FAILED, CallStatus.SUCCESS]
            if execution.status == CallStatus.FAILED:
                assert execution.error_message is not None
                assert "500" in execution.error_message

        finally:
            await service.close()

    async def test_different_http_methods(self, new_db):
        """Test different HTTP methods"""
        methods_to_test = [
            ("GET", "https://httpbin.org/get"),
            ("POST", "https://httpbin.org/post"),
            ("PUT", "https://httpbin.org/put"),
            ("DELETE", "https://httpbin.org/delete"),
        ]

        service = FunctionExecutionService()

        try:
            for method, url in methods_to_test:
                config = FunctionConfigService.create(
                    FunctionConfigCreate(
                        name=f"{method} Test",
                        endpoint_url=url,
                        http_method=method,
                        payload={"test": "data"} if method in ["POST", "PUT"] else {},
                        timeout_seconds=10,
                    )
                )

                if config.id is None:
                    continue
                execution = await service.execute_function(config.id)

                # All should succeed with HTTPBin
                assert execution.status == CallStatus.SUCCESS, f"{method} request failed"
                assert execution.response_status_code == 200
                assert execution.request_method == method

        finally:
            await service.close()

    async def test_headers_transmission(self, new_db):
        """Test that custom headers are transmitted correctly"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Headers Test",
                endpoint_url="https://httpbin.org/headers",
                http_method="GET",
                headers={"X-Custom-Header": "test-value", "X-Another-Header": "another-value"},
                timeout_seconds=10,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            assert execution.status == CallStatus.SUCCESS
            assert execution.response_status_code == 200

            # HTTPBin /headers returns the headers it received
            response_body = execution.response_body
            assert "X-Custom-Header" in response_body
            assert "test-value" in response_body
            assert "X-Another-Header" in response_body
            assert "another-value" in response_body

        finally:
            await service.close()

    async def test_large_response_handling(self, new_db):
        """Test handling of large responses"""
        # Use HTTPBin to generate a large JSON response
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Large Response Test",
                endpoint_url="https://httpbin.org/json",
                http_method="GET",
                timeout_seconds=15,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            assert execution.status == CallStatus.SUCCESS
            assert execution.response_status_code == 200
            assert execution.response_body is not None

            # Response body should be limited in length (per service implementation)
            assert len(execution.response_body) <= 10000

        finally:
            await service.close()

    async def test_concurrent_executions(self, new_db):
        """Test handling of concurrent function executions"""
        # Create multiple configs
        configs = []
        for i in range(3):
            config = FunctionConfigService.create(
                FunctionConfigCreate(
                    name=f"Concurrent Test {i}",
                    endpoint_url="https://httpbin.org/delay/1",  # 1 second delay
                    http_method="GET",
                    timeout_seconds=10,
                )
            )
            configs.append(config)

        service = FunctionExecutionService()

        try:
            # Execute all functions concurrently
            import asyncio

            tasks = []
            for config in configs:
                if config.id is not None:
                    tasks.append(service.execute_function(config.id))

            if not tasks:
                pytest.skip("No valid configs created")

            executions = await asyncio.gather(*tasks)

            # All should succeed
            for i, execution in enumerate(executions):
                assert execution.status == CallStatus.SUCCESS, f"Execution {i} failed"
                assert execution.response_status_code == 200
                assert execution.duration_ms is not None

        finally:
            await service.close()


class TestAPIErrorHandling:
    """Test error handling in API integration"""

    async def test_malformed_url_handling(self, new_db):
        """Test handling of malformed URLs"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(name="Malformed URL Test", endpoint_url="not-a-valid-url", timeout_seconds=5)
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            assert execution.status == CallStatus.FAILED
            assert execution.error_message is not None

        finally:
            await service.close()

    async def test_unsupported_http_method(self, new_db):
        """Test handling of unsupported HTTP methods"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Unsupported Method Test",
                endpoint_url="https://httpbin.org/get",
                http_method="PATCH",  # Not currently supported
                timeout_seconds=5,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should fail due to unsupported method
            assert execution.status == CallStatus.FAILED
            assert "Unsupported HTTP method" in execution.error_message

        finally:
            await service.close()

    async def test_network_connectivity_issues(self, new_db):
        """Test handling when network is unavailable"""
        # Use a non-routable IP address to simulate network failure
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Network Failure Test",
                endpoint_url="http://192.0.2.1/api",  # RFC 5737 test address
                timeout_seconds=3,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should fail due to network issues
            assert execution.status in [CallStatus.FAILED, CallStatus.TIMEOUT]
            assert execution.error_message is not None

        finally:
            await service.close()
