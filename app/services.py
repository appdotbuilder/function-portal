"""
Service layer for managing function configurations and executions.
This module provides business logic separate from UI components.
"""

import httpx
from datetime import datetime
from typing import List, Optional
from sqlmodel import select, desc

from app.database import get_session
from app.models import FunctionConfig, FunctionExecution, FunctionConfigCreate, CallStatus, ExecutionSummary


class FunctionConfigService:
    """Service for managing function configurations"""

    @staticmethod
    def get_all_active() -> List[FunctionConfig]:
        """Get all active function configurations ordered by display_order"""
        with get_session() as session:
            from sqlmodel import asc

            statement = (
                select(FunctionConfig)
                .where(FunctionConfig.is_active)
                .order_by(asc(FunctionConfig.display_order), asc(FunctionConfig.name))
            )
            return list(session.exec(statement))

    @staticmethod
    def get_by_id(config_id: int) -> Optional[FunctionConfig]:
        """Get function configuration by ID"""
        with get_session() as session:
            return session.get(FunctionConfig, config_id)

    @staticmethod
    def create(config_data: FunctionConfigCreate) -> FunctionConfig:
        """Create a new function configuration"""
        with get_session() as session:
            config = FunctionConfig(**config_data.model_dump())
            config.updated_at = datetime.utcnow()
            session.add(config)
            session.commit()
            session.refresh(config)
            return config

    @staticmethod
    def delete(config_id: int) -> bool:
        """Delete a function configuration"""
        with get_session() as session:
            config = session.get(FunctionConfig, config_id)
            if config is None:
                return False
            session.delete(config)
            session.commit()
            return True


class FunctionExecutionService:
    """Service for managing function executions and API calls"""

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def execute_function(self, config_id: int) -> FunctionExecution:
        """Execute a function based on its configuration"""
        with get_session() as session:
            config = session.get(FunctionConfig, config_id)
            if config is None:
                raise ValueError(f"Function configuration {config_id} not found")

            # Create execution record
            execution = FunctionExecution(
                function_config_id=config_id,
                status=CallStatus.RUNNING,
                started_at=datetime.utcnow(),
                request_url=config.endpoint_url,
                request_method=config.http_method,
                request_headers=config.headers,
                request_payload=config.payload,
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)

            execution_id = execution.id
            if execution_id is None:
                raise ValueError("Failed to create execution record")

            # Execute the API call
            await self._execute_api_call(execution_id, config)

            # Return updated execution record
            session.refresh(execution)
            return execution

    async def _execute_api_call(self, execution_id: int, config: FunctionConfig) -> None:
        """Execute the actual API call and update execution record"""
        start_time = datetime.utcnow()

        try:
            # Prepare request
            method = config.http_method.upper()
            headers = config.headers.copy() if config.headers else {}

            # Make the API call based on method
            match method:
                case "GET":
                    response = await self.client.get(
                        config.endpoint_url, headers=headers, timeout=config.timeout_seconds
                    )
                case "POST":
                    response = await self.client.post(
                        config.endpoint_url,
                        headers=headers,
                        json=config.payload if config.payload else None,
                        timeout=config.timeout_seconds,
                    )
                case "PUT":
                    response = await self.client.put(
                        config.endpoint_url,
                        headers=headers,
                        json=config.payload if config.payload else None,
                        timeout=config.timeout_seconds,
                    )
                case "DELETE":
                    response = await self.client.delete(
                        config.endpoint_url, headers=headers, timeout=config.timeout_seconds
                    )
                case _:
                    raise ValueError(f"Unsupported HTTP method: {method}")

            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update execution record with success
            with get_session() as session:
                execution = session.get(FunctionExecution, execution_id)
                if execution is not None:
                    execution.status = CallStatus.SUCCESS
                    execution.completed_at = end_time
                    execution.duration_ms = duration_ms
                    execution.response_status_code = response.status_code
                    execution.response_headers = dict(response.headers)
                    execution.response_body = response.text[:10000]  # Limit response size
                    session.add(execution)
                    session.commit()

        except httpx.TimeoutException:
            await self._mark_execution_failed(execution_id, "Request timed out", CallStatus.TIMEOUT)
        except httpx.HTTPStatusError as e:
            await self._mark_execution_failed(execution_id, f"HTTP {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:
            await self._mark_execution_failed(execution_id, str(e))

    async def _mark_execution_failed(
        self, execution_id: int, error_message: str, status: CallStatus = CallStatus.FAILED
    ) -> None:
        """Mark execution as failed with error message"""
        with get_session() as session:
            execution = session.get(FunctionExecution, execution_id)
            if execution is not None:
                execution.status = status
                execution.completed_at = datetime.utcnow()
                execution.error_message = error_message[:1000]  # Limit error message size
                if execution.started_at:
                    duration = datetime.utcnow() - execution.started_at
                    execution.duration_ms = int(duration.total_seconds() * 1000)
                session.add(execution)
                session.commit()

    @staticmethod
    def get_recent_executions(limit: int = 20) -> List[ExecutionSummary]:
        """Get recent function executions with summary information"""
        with get_session() as session:
            statement = (
                select(FunctionExecution, FunctionConfig.name)
                .join(FunctionConfig)
                .order_by(desc(FunctionExecution.started_at))
                .limit(limit)
            )

            results = session.exec(statement).all()

            summaries = []
            for execution, function_name in results:
                success = (
                    execution.status == CallStatus.SUCCESS
                    and execution.response_status_code is not None
                    and 200 <= execution.response_status_code < 300
                )

                if execution.id is None:
                    continue

                summary = ExecutionSummary(
                    id=execution.id,
                    function_name=function_name,
                    status=execution.status,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration_ms=execution.duration_ms,
                    response_status_code=execution.response_status_code,
                    success=success,
                )
                summaries.append(summary)

            return summaries

    @staticmethod
    def get_execution_details(execution_id: int) -> Optional[FunctionExecution]:
        """Get detailed execution information"""
        with get_session() as session:
            return session.get(FunctionExecution, execution_id)

    async def close(self) -> None:
        """Close the HTTP client"""
        await self.client.aclose()


def seed_sample_data() -> None:
    """Create sample function configurations for demonstration"""
    sample_configs = [
        FunctionConfigCreate(
            name="JSONPlaceholder Posts",
            description="Fetch sample posts from JSONPlaceholder API",
            endpoint_url="https://jsonplaceholder.typicode.com/posts",
            http_method="GET",
            timeout_seconds=10,
            button_color="primary",
            display_order=1,
        ),
        FunctionConfigCreate(
            name="Create Post",
            description="Create a new post via JSONPlaceholder API",
            endpoint_url="https://jsonplaceholder.typicode.com/posts",
            http_method="POST",
            headers={"Content-Type": "application/json"},
            payload={"title": "Sample Post", "body": "This is a sample post created from the UI", "userId": 1},
            timeout_seconds=15,
            button_color="positive",
            display_order=2,
        ),
        FunctionConfigCreate(
            name="HTTPBin Echo",
            description="Test API call with HTTPBin echo service",
            endpoint_url="https://httpbin.org/post",
            http_method="POST",
            headers={"Content-Type": "application/json"},
            payload={"message": "Hello from Function Trigger App!", "timestamp": "2024-01-01T00:00:00Z"},
            timeout_seconds=20,
            button_color="accent",
            display_order=3,
        ),
    ]

    service = FunctionConfigService()
    for config_data in sample_configs:
        try:
            service.create(config_data)
        except Exception as e:
            # Config might already exist, continue with others
            import logging

            logging.getLogger(__name__).info(f"Skipping sample config {config_data.name}: {e}")
