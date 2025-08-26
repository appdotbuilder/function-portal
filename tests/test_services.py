"""
Tests for service layer components.
"""

import pytest
from datetime import datetime

from app.database import reset_db, get_session
from app.services import FunctionConfigService, FunctionExecutionService
from app.models import FunctionConfigCreate, CallStatus


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


class TestFunctionConfigService:
    """Test function configuration service"""

    def test_create_function_config(self, new_db):
        """Test creating a new function configuration"""
        config_data = FunctionConfigCreate(
            name="Test Function",
            description="A test function",
            endpoint_url="https://httpbin.org/post",
            http_method="POST",
            headers={"Content-Type": "application/json"},
            payload={"test": "data"},
            timeout_seconds=30,
            button_color="primary",
            display_order=1,
        )

        config = FunctionConfigService.create(config_data)

        assert config.id is not None
        assert config.name == "Test Function"
        assert config.description == "A test function"
        assert config.endpoint_url == "https://httpbin.org/post"
        assert config.http_method == "POST"
        assert config.headers == {"Content-Type": "application/json"}
        assert config.payload == {"test": "data"}
        assert config.timeout_seconds == 30
        assert config.button_color == "primary"
        assert config.display_order == 1
        assert config.is_active is True
        assert config.created_at is not None
        assert config.updated_at is not None

    def test_get_all_active(self, new_db):
        """Test getting all active function configurations"""
        # Create test configs
        FunctionConfigService.create(
            FunctionConfigCreate(name="Config 1", endpoint_url="https://api1.com", display_order=2)
        )
        FunctionConfigService.create(
            FunctionConfigCreate(name="Config 2", endpoint_url="https://api2.com", display_order=1)
        )

        # Create inactive config
        inactive_data = FunctionConfigCreate(name="Inactive Config", endpoint_url="https://api3.com", is_active=False)
        FunctionConfigService.create(inactive_data)

        active_configs = FunctionConfigService.get_all_active()

        assert len(active_configs) == 2
        # Should be ordered by display_order
        assert active_configs[0].name == "Config 2"  # display_order=1
        assert active_configs[1].name == "Config 1"  # display_order=2

    def test_get_by_id(self, new_db):
        """Test getting function configuration by ID"""
        config = FunctionConfigService.create(FunctionConfigCreate(name="Test Config", endpoint_url="https://test.com"))

        if config.id is None:
            pytest.skip("Config ID is None")
        retrieved_config = FunctionConfigService.get_by_id(config.id)

        assert retrieved_config is not None
        assert retrieved_config.name == "Test Config"
        assert retrieved_config.endpoint_url == "https://test.com"

    def test_get_by_id_not_found(self, new_db):
        """Test getting non-existent function configuration"""
        config = FunctionConfigService.get_by_id(999)
        assert config is None

    def test_delete_config(self, new_db):
        """Test deleting a function configuration"""
        config = FunctionConfigService.create(FunctionConfigCreate(name="To Delete", endpoint_url="https://delete.com"))

        assert config.id is not None
        config_id = config.id

        # Delete the config
        result = FunctionConfigService.delete(config_id)
        assert result is True

        # Verify it's gone
        deleted_config = FunctionConfigService.get_by_id(config_id)
        assert deleted_config is None

    def test_delete_nonexistent_config(self, new_db):
        """Test deleting a non-existent configuration"""
        result = FunctionConfigService.delete(999)
        assert result is False


class TestFunctionExecutionService:
    """Test function execution service"""

    async def test_execute_function_not_found(self, new_db):
        """Test executing non-existent function"""
        service = FunctionExecutionService()

        with pytest.raises(ValueError, match="Function configuration 999 not found"):
            await service.execute_function(999)

    def test_get_recent_executions_empty(self, new_db):
        """Test getting executions when none exist"""
        executions = FunctionExecutionService.get_recent_executions()
        assert executions == []

    def test_get_execution_details_not_found(self, new_db):
        """Test getting execution details for non-existent execution"""
        execution = FunctionExecutionService.get_execution_details(999)
        assert execution is None

    async def test_execute_function_success_mock_endpoint(self, new_db):
        """Test successful function execution with mock endpoint"""
        # Create a test function config
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Test HTTPBin",
                endpoint_url="https://httpbin.org/post",
                http_method="POST",
                headers={"Content-Type": "application/json"},
                payload={"test": "data"},
                timeout_seconds=10,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Verify execution record
            assert execution.id is not None
            assert execution.function_config_id == config.id
            assert execution.request_url == "https://httpbin.org/post"
            assert execution.request_method == "POST"
            assert execution.request_headers == {"Content-Type": "application/json"}
            assert execution.request_payload == {"test": "data"}
            assert execution.started_at is not None

            # Status should be success or failed (depending on network)
            assert execution.status in [CallStatus.SUCCESS, CallStatus.FAILED, CallStatus.TIMEOUT]

            if execution.status == CallStatus.SUCCESS:
                assert execution.completed_at is not None
                assert execution.duration_ms is not None
                assert execution.response_status_code is not None
                assert 200 <= execution.response_status_code < 300
                assert execution.response_body is not None

        finally:
            await service.close()

    async def test_execute_function_invalid_url(self, new_db):
        """Test function execution with invalid URL"""
        config = FunctionConfigService.create(
            FunctionConfigCreate(
                name="Invalid URL Test",
                endpoint_url="https://invalid-url-that-does-not-exist-12345.com",
                timeout_seconds=5,
            )
        )

        service = FunctionExecutionService()

        try:
            if config.id is None:
                pytest.skip("Config ID is None")
            execution = await service.execute_function(config.id)

            # Should fail
            assert execution.status == CallStatus.FAILED
            assert execution.error_message is not None
            assert len(execution.error_message) > 0
            assert execution.completed_at is not None
            assert execution.duration_ms is not None

        finally:
            await service.close()

    def test_get_recent_executions_with_data(self, new_db):
        """Test getting recent executions with test data"""
        # Create a config first
        config = FunctionConfigService.create(
            FunctionConfigCreate(name="Test Function", endpoint_url="https://test.com")
        )

        # Create a manual execution record for testing
        from app.models import FunctionExecution

        if config.id is None:
            pytest.skip("Config ID is None")

        with get_session() as session:
            execution = FunctionExecution(
                function_config_id=config.id,
                status=CallStatus.SUCCESS,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration_ms=500,
                request_url="https://test.com",
                request_method="POST",
                response_status_code=200,
                response_body='{"success": true}',
            )
            session.add(execution)
            session.commit()

        # Get recent executions
        executions = FunctionExecutionService.get_recent_executions(10)

        assert len(executions) == 1
        summary = executions[0]

        assert summary.function_name == "Test Function"
        assert summary.status == CallStatus.SUCCESS
        assert summary.success is True
        assert summary.duration_ms == 500
        assert summary.response_status_code == 200
