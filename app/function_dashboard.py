"""
Main dashboard module for displaying and triggering function configurations.
"""

import asyncio
from typing import Dict
from nicegui import ui

from app.services import FunctionConfigService, FunctionExecutionService
from app.models import FunctionConfig, CallStatus


class FunctionDashboard:
    """Dashboard for managing and executing functions"""

    def __init__(self):
        self.execution_service = FunctionExecutionService()
        self.executing_functions: Dict[int, bool] = {}
        self.status_container = None
        self.execution_log = None

    def create(self) -> None:
        """Create the function dashboard UI"""

        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            # Header section
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Function Trigger Dashboard").classes("text-3xl font-bold text-gray-800")
                ui.button("Add New Function", icon="add", on_click=lambda: ui.navigate.to("/config")).classes(
                    "bg-primary text-white px-4 py-2 rounded-lg shadow hover:shadow-lg"
                )

            # Function buttons section
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
                ui.label("Available Functions").classes("text-xl font-semibold mb-4")
                self._create_function_buttons()

            # Status and execution log section
            with ui.row().classes("w-full gap-6"):
                # Current status
                with ui.card().classes("flex-1 p-6 shadow-lg rounded-xl"):
                    ui.label("Execution Status").classes("text-xl font-semibold mb-4")
                    self.status_container = ui.column().classes("gap-2")
                    self._update_status_display()

                # Recent executions
                with ui.card().classes("flex-1 p-6 shadow-lg rounded-xl"):
                    ui.label("Recent Executions").classes("text-xl font-semibold mb-4")
                    self.execution_log = ui.column().classes("gap-2 max-h-80 overflow-auto")
                    self._update_execution_log()

    def _create_function_buttons(self) -> None:
        """Create buttons for all active function configurations"""
        configs = FunctionConfigService.get_all_active()

        if not configs:
            ui.label("No functions configured. Add some functions to get started.").classes("text-gray-500 italic p-4")
            return

        with ui.row().classes("w-full gap-4 flex-wrap"):
            for config in configs:
                self._create_function_button(config)

    def _create_function_button(self, config: FunctionConfig) -> None:
        """Create a single function button"""
        if config.id is None:
            return

        config_id = config.id
        is_executing = self.executing_functions.get(config_id, False)

        # Button styling based on method and status
        button_classes = "px-6 py-4 rounded-lg shadow hover:shadow-lg transition-all text-white font-medium"

        if is_executing:
            button_classes += " opacity-60 cursor-not-allowed"
            button_text = f"⏳ {config.name}"
            button_color = "secondary"
        else:
            button_text = config.name
            button_color = config.button_color

        with ui.column().classes("min-w-48 gap-2"):
            button = ui.button(
                button_text,
                icon="play_arrow" if not is_executing else "hourglass_empty",
                on_click=lambda _, c_id=config_id: asyncio.create_task(self._execute_function(c_id)),
            ).classes(button_classes)
            button.props(f"color={button_color}")

            # Method and endpoint info
            method_color = {"GET": "blue", "POST": "green", "PUT": "orange", "DELETE": "red"}.get(
                config.http_method, "gray"
            )

            ui.label(f"{config.http_method} • {self._truncate_url(config.endpoint_url)}").classes(
                f"text-sm text-{method_color}-600"
            )

            if config.description:
                ui.label(config.description).classes("text-xs text-gray-500 leading-tight")

    async def _execute_function(self, config_id: int) -> None:
        """Execute a function and update the UI"""
        if self.executing_functions.get(config_id, False):
            return  # Already executing

        try:
            # Mark as executing
            self.executing_functions[config_id] = True
            self._refresh_dashboard()

            # Update status
            config = FunctionConfigService.get_by_id(config_id)
            if config:
                ui.notify(f"Executing {config.name}...", type="info")

            # Execute the function
            execution = await self.execution_service.execute_function(config_id)

            # Show result notification
            if execution.status == CallStatus.SUCCESS:
                ui.notify(f"✅ {config.name if config else 'Function'} completed successfully!", type="positive")
            elif execution.status == CallStatus.TIMEOUT:
                ui.notify(f"⏰ {config.name if config else 'Function'} timed out", type="warning")
            else:
                ui.notify(
                    f"❌ {config.name if config else 'Function'} failed: {execution.error_message}", type="negative"
                )

        except Exception as e:
            ui.notify(f"Error executing function: {str(e)}", type="negative")
        finally:
            # Mark as not executing
            self.executing_functions[config_id] = False
            self._refresh_dashboard()
            self._update_status_display()
            self._update_execution_log()

    def _update_status_display(self) -> None:
        """Update the status display area"""
        if not self.status_container:
            return

        self.status_container.clear()

        executing_count = sum(1 for is_exec in self.executing_functions.values() if is_exec)

        if executing_count > 0:
            with self.status_container:
                ui.label(f"⏳ {executing_count} function(s) executing...").classes("text-orange-600 font-medium")
        else:
            with self.status_container:
                ui.label("✅ All functions idle").classes("text-green-600 font-medium")

    def _update_execution_log(self) -> None:
        """Update the execution log display"""
        if not self.execution_log:
            return

        self.execution_log.clear()

        try:
            recent_executions = FunctionExecutionService.get_recent_executions(10)

            with self.execution_log:
                if not recent_executions:
                    ui.label("No executions yet").classes("text-gray-500 italic")
                    return

                for execution in recent_executions:
                    self._create_execution_log_item(execution)
        except Exception as e:
            with self.execution_log:
                ui.label(f"Error loading executions: {str(e)}").classes("text-red-500")

    def _create_execution_log_item(self, execution) -> None:
        """Create a single execution log item"""
        # Status styling
        status_colors = {
            CallStatus.SUCCESS: ("text-green-600", "✅"),
            CallStatus.FAILED: ("text-red-600", "❌"),
            CallStatus.TIMEOUT: ("text-orange-600", "⏰"),
            CallStatus.RUNNING: ("text-blue-600", "⏳"),
            CallStatus.PENDING: ("text-gray-600", "⏸️"),
        }

        color_class, icon = status_colors.get(execution.status, ("text-gray-600", "❓"))

        # Format timestamp
        time_str = execution.started_at.strftime("%H:%M:%S")

        # Duration display
        duration_display = (
            execution.duration_display
            if hasattr(execution, "duration_display")
            else (f"{execution.duration_ms}ms" if execution.duration_ms else "N/A")
        )

        with ui.row().classes("w-full items-center justify-between p-2 border-b border-gray-100 hover:bg-gray-50"):
            with ui.row().classes("items-center gap-2"):
                ui.label(icon).classes("text-lg")
                ui.label(execution.function_name).classes("font-medium text-gray-800")
                ui.label(time_str).classes("text-xs text-gray-500")

            with ui.row().classes("items-center gap-2"):
                if execution.response_status_code:
                    status_color = "text-green-600" if 200 <= execution.response_status_code < 300 else "text-red-600"
                    ui.label(str(execution.response_status_code)).classes(f"text-xs {status_color} font-mono")
                ui.label(duration_display).classes("text-xs text-gray-500 font-mono")

    def _refresh_dashboard(self) -> None:
        """Refresh the entire dashboard"""
        # This would ideally use @ui.refreshable, but for now we'll update specific components
        pass

    @staticmethod
    def _truncate_url(url: str, max_length: int = 40) -> str:
        """Truncate URL for display"""
        if len(url) <= max_length:
            return url
        return f"{url[: max_length - 3]}..."


def create() -> None:
    """Create the function dashboard page"""
    dashboard = FunctionDashboard()

    @ui.page("/")
    async def index():
        dashboard.create()

        # Auto-refresh execution log every 10 seconds
        ui.timer(10.0, dashboard._update_execution_log)
        ui.timer(5.0, dashboard._update_status_display)
