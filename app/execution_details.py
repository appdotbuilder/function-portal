"""
Execution details module for viewing detailed information about function executions.
"""

import json
from typing import Optional
from nicegui import ui

from app.services import FunctionExecutionService, FunctionConfigService
from app.models import FunctionExecution, FunctionConfig, CallStatus


class ExecutionDetailsView:
    """View for displaying detailed execution information"""

    def __init__(self):
        self.execution_service = FunctionExecutionService()

    def create(self, execution_id: int) -> None:
        """Create the execution details view"""

        # Get execution details
        execution = FunctionExecutionService.get_execution_details(execution_id)
        if execution is None:
            self._show_not_found()
            return

        # Get function config details
        config = FunctionConfigService.get_by_id(execution.function_config_id)

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            # Header with navigation
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label(f"Execution Details #{execution_id}").classes("text-3xl font-bold text-gray-800")
                with ui.row().classes("gap-2"):
                    ui.button(
                        "View All Executions", icon="list", on_click=lambda: ui.navigate.to("/executions")
                    ).classes("px-4 py-2 text-gray-600 border border-gray-300 rounded-lg")
                    ui.button("Back to Dashboard", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes(
                        "bg-primary text-white px-4 py-2 rounded-lg"
                    )

            # Status overview card
            self._create_status_card(execution, config)

            # Request and response details
            with ui.row().classes("w-full gap-6"):
                self._create_request_card(execution)
                self._create_response_card(execution)

            # Configuration details if available
            if config:
                self._create_config_card(config)

    def _create_status_card(self, execution: FunctionExecution, config: Optional[FunctionConfig]) -> None:
        """Create the status overview card"""
        with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
            ui.label("Execution Overview").classes("text-xl font-semibold mb-4")

            # Status indicator
            status_colors = {
                CallStatus.SUCCESS: ("bg-green-100 text-green-800", "✅ Success"),
                CallStatus.FAILED: ("bg-red-100 text-red-800", "❌ Failed"),
                CallStatus.TIMEOUT: ("bg-orange-100 text-orange-800", "⏰ Timeout"),
                CallStatus.RUNNING: ("bg-blue-100 text-blue-800", "⏳ Running"),
                CallStatus.PENDING: ("bg-gray-100 text-gray-800", "⏸️ Pending"),
            }

            color_class, status_text = status_colors.get(execution.status, ("bg-gray-100 text-gray-800", "❓ Unknown"))

            with ui.row().classes("w-full items-center gap-6 mb-4"):
                ui.label(status_text).classes(f"px-4 py-2 rounded-full font-medium {color_class}")

                if execution.duration_ms is not None:
                    duration_text = (
                        f"{execution.duration_ms}ms"
                        if execution.duration_ms < 1000
                        else f"{execution.duration_ms / 1000:.1f}s"
                    )
                    ui.label(f"Duration: {duration_text}").classes("text-gray-600 font-mono")

            # Execution details grid
            with ui.row().classes("w-full gap-8"):
                with ui.column().classes("flex-1 gap-2"):
                    self._create_detail_item("Function Name", config.name if config else "Unknown")
                    self._create_detail_item("Started", execution.started_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
                    if execution.completed_at:
                        self._create_detail_item("Completed", execution.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC"))

                with ui.column().classes("flex-1 gap-2"):
                    self._create_detail_item("Request Method", execution.request_method)
                    self._create_detail_item("Request URL", execution.request_url)
                    if execution.response_status_code:
                        status_color = (
                            "text-green-600" if 200 <= execution.response_status_code < 300 else "text-red-600"
                        )
                        ui.label("Response Status:").classes("text-sm font-medium text-gray-700")
                        ui.label(str(execution.response_status_code)).classes(
                            f"text-lg font-mono {status_color} font-bold"
                        )

            # Error message if present
            if execution.error_message:
                ui.separator().classes("my-4")
                ui.label("Error Details").classes("text-sm font-medium text-red-700 mb-2")
                ui.label(execution.error_message).classes(
                    "text-red-600 bg-red-50 p-3 rounded border-l-4 border-red-400 font-mono text-sm"
                )

    def _create_request_card(self, execution: FunctionExecution) -> None:
        """Create the request details card"""
        with ui.card().classes("flex-1 p-6 shadow-lg rounded-xl"):
            ui.label("Request Details").classes("text-xl font-semibold mb-4")

            # Request headers
            if execution.request_headers:
                ui.label("Headers:").classes("text-sm font-medium text-gray-700 mb-2")
                headers_json = json.dumps(execution.request_headers, indent=2)
                ui.code(headers_json).classes("w-full p-3 bg-gray-50 rounded border text-sm max-h-32 overflow-auto")

            # Request payload
            if execution.request_payload:
                ui.label("Payload:").classes("text-sm font-medium text-gray-700 mb-2 mt-4")
                payload_json = json.dumps(execution.request_payload, indent=2)
                ui.code(payload_json).classes("w-full p-3 bg-gray-50 rounded border text-sm max-h-48 overflow-auto")

            if not execution.request_headers and not execution.request_payload:
                ui.label("No request data").classes("text-gray-500 italic")

    def _create_response_card(self, execution: FunctionExecution) -> None:
        """Create the response details card"""
        with ui.card().classes("flex-1 p-6 shadow-lg rounded-xl"):
            ui.label("Response Details").classes("text-xl font-semibold mb-4")

            # Response headers
            if execution.response_headers:
                ui.label("Response Headers:").classes("text-sm font-medium text-gray-700 mb-2")
                headers_json = json.dumps(execution.response_headers, indent=2)
                ui.code(headers_json).classes("w-full p-3 bg-gray-50 rounded border text-sm max-h-32 overflow-auto")

            # Response body
            if execution.response_body:
                ui.label("Response Body:").classes("text-sm font-medium text-gray-700 mb-2 mt-4")

                # Try to format as JSON if possible
                try:
                    parsed_body = json.loads(execution.response_body)
                    formatted_body = json.dumps(parsed_body, indent=2)
                    ui.code(formatted_body).classes(
                        "w-full p-3 bg-gray-50 rounded border text-sm max-h-64 overflow-auto"
                    )
                except json.JSONDecodeError as e:
                    # Show as plain text
                    import logging

                    logging.getLogger(__name__).debug(f"Response body is not valid JSON: {e}")
                    ui.code(execution.response_body).classes(
                        "w-full p-3 bg-gray-50 rounded border text-sm max-h-64 overflow-auto whitespace-pre-wrap"
                    )

            if not execution.response_headers and not execution.response_body:
                ui.label("No response data").classes("text-gray-500 italic")

    def _create_config_card(self, config: FunctionConfig) -> None:
        """Create the configuration details card"""
        with ui.card().classes("w-full p-6 shadow-lg rounded-xl mt-6"):
            ui.label("Function Configuration").classes("text-xl font-semibold mb-4")

            with ui.row().classes("w-full gap-8"):
                with ui.column().classes("flex-1 gap-2"):
                    self._create_detail_item("Name", config.name)
                    self._create_detail_item("Description", config.description or "No description")
                    self._create_detail_item("HTTP Method", config.http_method)
                    self._create_detail_item("Timeout", f"{config.timeout_seconds}s")

                with ui.column().classes("flex-1 gap-2"):
                    self._create_detail_item("Endpoint URL", config.endpoint_url)
                    self._create_detail_item("Button Color", config.button_color)
                    self._create_detail_item("Display Order", str(config.display_order))
                    self._create_detail_item("Active", "Yes" if config.is_active else "No")

    def _create_detail_item(self, label: str, value: str) -> None:
        """Create a detail item with label and value"""
        ui.label(f"{label}:").classes("text-sm font-medium text-gray-700")
        ui.label(value).classes("text-sm text-gray-900 mb-2 break-all")

    def _show_not_found(self) -> None:
        """Show not found message"""
        with ui.column().classes("w-full max-w-2xl mx-auto p-6 text-center"):
            ui.icon("error", size="4rem").classes("text-red-500 mb-4")
            ui.label("Execution Not Found").classes("text-2xl font-bold text-gray-800 mb-2")
            ui.label("The requested execution details could not be found.").classes("text-gray-600 mb-6")
            ui.button("Back to Dashboard", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes(
                "bg-primary text-white px-6 py-3 rounded-lg"
            )


def create() -> None:
    """Create the execution details pages"""

    @ui.page("/execution/{execution_id}")
    def execution_details(execution_id: int):
        view = ExecutionDetailsView()
        view.create(execution_id)
