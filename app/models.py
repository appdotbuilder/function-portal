from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class CallStatus(str, Enum):
    """Status of an API call execution"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class FunctionConfig(SQLModel, table=True):
    """Configuration for external functions that can be triggered via buttons"""

    __tablename__ = "function_configs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="Display name for the function")
    description: str = Field(default="", max_length=500, description="Description of what this function does")
    endpoint_url: str = Field(max_length=500, description="API endpoint URL to call")
    http_method: str = Field(default="POST", max_length=10, description="HTTP method (GET, POST, etc.)")
    headers: Dict[str, str] = Field(default={}, sa_column=Column(JSON), description="HTTP headers to include")
    payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSON), description="Request payload/body")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    is_active: bool = Field(default=True, description="Whether this function is available for execution")
    button_color: str = Field(default="primary", max_length=20, description="UI button color/style")
    display_order: int = Field(default=0, description="Order for displaying buttons")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to execution records
    executions: List["FunctionExecution"] = Relationship(back_populates="function_config")


class FunctionCall(SQLModel, table=True):
    """Model for storing external API call information"""

    __tablename__ = "function_calls"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    parameters: str = Field(default="", description="Input parameters for the API call as JSON string")
    endpoint: str = Field(max_length=500, description="URL of the external API to be called")
    api_key: Optional[str] = Field(default=None, max_length=500, description="Authentication token or API key")
    error_message: Optional[str] = Field(default=None, max_length=1000, description="Error message from API call")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FunctionExecution(SQLModel, table=True):
    """Record of an external function call execution"""

    __tablename__ = "function_executions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    function_config_id: int = Field(foreign_key="function_configs.id")
    status: CallStatus = Field(default=CallStatus.PENDING, description="Current status of the execution")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, description="When the execution completed")
    duration_ms: Optional[int] = Field(default=None, description="Execution duration in milliseconds")

    # Request details
    request_url: str = Field(max_length=500, description="Actual URL called")
    request_method: str = Field(max_length=10, description="HTTP method used")
    request_headers: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    request_payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Response details
    response_status_code: Optional[int] = Field(default=None, description="HTTP response status code")
    response_headers: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    response_body: str = Field(default="", description="Response body content")
    error_message: str = Field(default="", max_length=1000, description="Error message if execution failed")

    # Relationship to function configuration
    function_config: FunctionConfig = Relationship(back_populates="executions")


# Non-persistent schemas for validation and API


class FunctionCallCreate(SQLModel, table=False):
    """Schema for creating a new function call"""

    parameters: str = Field(default="", description="Input parameters as JSON string")
    endpoint: str = Field(max_length=500, description="API endpoint URL")
    api_key: Optional[str] = Field(default=None, max_length=500, description="API key or token")


class FunctionCallUpdate(SQLModel, table=False):
    """Schema for updating a function call"""

    parameters: Optional[str] = Field(default=None, description="Input parameters as JSON string")
    endpoint: Optional[str] = Field(default=None, max_length=500, description="API endpoint URL")
    api_key: Optional[str] = Field(default=None, max_length=500, description="API key or token")
    error_message: Optional[str] = Field(default=None, max_length=1000, description="Error message")


class FunctionConfigCreate(SQLModel, table=False):
    """Schema for creating a new function configuration"""

    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    endpoint_url: str = Field(max_length=500)
    http_method: str = Field(default="POST", max_length=10)
    headers: Dict[str, str] = Field(default={})
    payload: Dict[str, Any] = Field(default={})
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    is_active: bool = Field(default=True)
    button_color: str = Field(default="primary", max_length=20)
    display_order: int = Field(default=0)


class FunctionConfigUpdate(SQLModel, table=False):
    """Schema for updating an existing function configuration"""

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    endpoint_url: Optional[str] = Field(default=None, max_length=500)
    http_method: Optional[str] = Field(default=None, max_length=10)
    headers: Optional[Dict[str, str]] = Field(default=None)
    payload: Optional[Dict[str, Any]] = Field(default=None)
    timeout_seconds: Optional[int] = Field(default=None, ge=1, le=300)
    is_active: Optional[bool] = Field(default=None)
    button_color: Optional[str] = Field(default=None, max_length=20)
    display_order: Optional[int] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FunctionExecutionCreate(SQLModel, table=False):
    """Schema for creating a new function execution record"""

    function_config_id: int
    request_url: str = Field(max_length=500)
    request_method: str = Field(max_length=10)
    request_headers: Dict[str, str] = Field(default={})
    request_payload: Dict[str, Any] = Field(default={})


class FunctionExecutionUpdate(SQLModel, table=False):
    """Schema for updating execution status and results"""

    status: Optional[CallStatus] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_ms: Optional[int] = Field(default=None)
    response_status_code: Optional[int] = Field(default=None)
    response_headers: Optional[Dict[str, str]] = Field(default=None)
    response_body: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=1000)


class ExecutionSummary(SQLModel, table=False):
    """Summary view of function execution for display"""

    id: int
    function_name: str
    status: CallStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    response_status_code: Optional[int]
    success: bool = Field(description="Whether the execution was successful")

    @property
    def duration_display(self) -> str:
        """Human-readable duration string"""
        if self.duration_ms is None:
            return "N/A"
        if self.duration_ms < 1000:
            return f"{self.duration_ms}ms"
        return f"{self.duration_ms / 1000:.1f}s"
