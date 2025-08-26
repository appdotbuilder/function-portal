"""
Main dashboard module for displaying and triggering function configurations.
"""

import asyncio
from typing import Dict, Optional
from nicegui import ui

from app.services import FunctionConfigService, FunctionExecutionService
from app.models import FunctionConfig, CallStatus


class FunctionDashboard:
    """Dashboard for managing and executing functions"""

    def __init__(self):
        self.execution_service = FunctionExecutionService()
        self.executing_functions: Dict[int, bool] = {}
        self.status_container: Optional[ui.column] = None
        self.function_buttons_container: Optional[ui.column] = None
        self.execution_log_container: Optional[ui.column] = None

    def create(self) -> None:
        """Create the function dashboard UI"""
        try:
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
                    self.function_buttons_container = ui.column().classes("w-full")
                    # Initial render of function buttons
                    self._render_function_buttons()

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
                        self.execution_log_container = ui.column().classes("gap-2 max-h-80 overflow-auto")
                        # Initial render of execution log
                        self._render_execution_log()

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Critical error in dashboard UI creation: {str(e)}", exc_info=True)
            raise

    @ui.refreshable
    def _create_function_buttons(self) -> None:
        """Refreshable method to create function buttons"""
        self._render_function_buttons()

    def _render_function_buttons(self) -> None:
        """Render function buttons for all active function configurations"""
        try:
            if self.function_buttons_container:
                self.function_buttons_container.clear()

            configs = FunctionConfigService.get_all_active()

            if not configs:
                ui.label("No functions configured. Add some functions to get started.").classes(
                    "text-gray-500 italic p-4"
                )
                ui.label("Click 'Add New Function' to create your first function.").classes("text-gray-400 text-sm p-2")
                return

            with ui.row().classes("w-full gap-4 flex-wrap"):
                for config in configs:
                    try:
                        self._create_function_button(config)
                    except Exception as e:
                        import logging

                        logging.getLogger(__name__).error(
                            f"Error creating button for config {config.id}: {str(e)}", exc_info=True
                        )
                        # Create a placeholder error button
                        ui.button(
                            f"⚠️ Error: {config.name if hasattr(config, 'name') and config.name else 'Unknown'}",
                            icon="error",
                        ).classes("px-4 py-2 bg-red-500 text-white rounded").props("disable")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error fetching function configurations: {str(e)}", exc_info=True)
            ui.label(f"⚠️ Unable to load function configurations: {str(e)}").classes("text-red-600 p-4")
            ui.label("This may be due to database connectivity issues.").classes("text-red-500 text-sm p-2")

    def _create_function_button(self, config: FunctionConfig) -> None:
        """Create a single function button"""
        if config.id is None:
            return

        try:
            config_id = config.id
            is_executing = self.executing_functions.get(config_id, False)

            # Button styling based on method and status
            button_classes = "px-6 py-4 rounded-lg shadow hover:shadow-lg transition-all text-white font-medium"

            # Safe access to config properties
            config_name = getattr(config, "name", f"Function {config_id}") or f"Function {config_id}"
            config_method = getattr(config, "http_method", "GET") or "GET"
            config_url = getattr(config, "endpoint_url", "Unknown URL") or "Unknown URL"
            config_description = getattr(config, "description", None)
            config_button_color = getattr(config, "button_color", "primary") or "primary"

            if is_executing:
                button_classes += " opacity-60 cursor-not-allowed"
                button_text = f"⏳ {config_name}"
                button_color = "secondary"
            else:
                button_text = config_name
                button_color = config_button_color

            with ui.column().classes("min-w-48 gap-2"):
                button = ui.button(
                    button_text,
                    icon="play_arrow" if not is_executing else "hourglass_empty",
                    on_click=lambda _, c_id=config_id: asyncio.create_task(self._execute_function(c_id)),
                ).classes(button_classes)

                try:
                    button.props(f"color={button_color}")
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).error(f"Error setting button color: {str(e)}", exc_info=True)
                    button.props("color=primary")  # Fallback color

                # Method and endpoint info
                method_color = {"GET": "blue", "POST": "green", "PUT": "orange", "DELETE": "red"}.get(
                    config_method, "gray"
                )

                try:
                    ui.label(f"{config_method} • {self._truncate_url(config_url)}").classes(
                        f"text-sm text-{method_color}-600"
                    )
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).error(f"Error creating method label: {str(e)}", exc_info=True)
                    ui.label(f"{config_method} • {config_url}").classes("text-sm text-gray-600")

                if config_description:
                    ui.label(config_description).classes("text-xs text-gray-500 leading-tight")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error creating function button for config {config.id}: {str(e)}", exc_info=True
            )

            # Create a minimal error button
            config_name = getattr(config, "name", "Unknown") if config else "Unknown"
            ui.button(f"⚠️ Error: {config_name}", icon="error").classes(
                "px-4 py-2 bg-red-500 text-white rounded opacity-60"
            ).props("disable")

    async def _execute_function(self, config_id: int) -> None:
        """Execute a function and update the UI"""
        if self.executing_functions.get(config_id, False):
            return  # Already executing

        config = None
        try:
            # Mark as executing
            self.executing_functions[config_id] = True
            self._refresh_dashboard()

            # Get configuration safely
            try:
                config = FunctionConfigService.get_by_id(config_id)
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error fetching config {config_id}: {str(e)}", exc_info=True)
                ui.notify(f"Error fetching function configuration: {str(e)}", type="negative")
                return

            if config:
                ui.notify(f"Executing {config.name}...", type="info")
            else:
                ui.notify(f"Executing function {config_id}...", type="info")

            # Execute the function
            try:
                execution = await self.execution_service.execute_function(config_id)

                # Show result notification
                function_name = config.name if config else f"Function {config_id}"

                if execution.status == CallStatus.SUCCESS:
                    ui.notify(f"✅ {function_name} completed successfully!", type="positive")
                elif execution.status == CallStatus.TIMEOUT:
                    ui.notify(f"⏰ {function_name} timed out", type="warning")
                else:
                    error_msg = getattr(execution, "error_message", "Unknown error")
                    ui.notify(f"❌ {function_name} failed: {error_msg}", type="negative")

            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error executing function {config_id}: {str(e)}", exc_info=True)
                function_name = config.name if config else f"Function {config_id}"
                ui.notify(f"❌ {function_name} execution failed: {str(e)}", type="negative")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Critical error in function execution {config_id}: {str(e)}", exc_info=True
            )
            ui.notify(f"Critical error executing function: {str(e)}", type="negative")

        finally:
            # Mark as not executing
            self.executing_functions[config_id] = False
            try:
                self._refresh_dashboard()
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(
                    f"Error updating UI after function execution: {str(e)}", exc_info=True
                )

    def _update_status_display(self) -> None:
        """Update the status display area"""
        if not self.status_container:
            return

        try:
            self.status_container.clear()

            executing_count = sum(1 for is_exec in self.executing_functions.values() if is_exec)

            with self.status_container:
                if executing_count > 0:
                    ui.label(f"⏳ {executing_count} function(s) executing...").classes("text-orange-600 font-medium")
                else:
                    ui.label("✅ All functions idle").classes("text-green-600 font-medium")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error updating status display: {str(e)}", exc_info=True)

            if self.status_container:
                try:
                    self.status_container.clear()
                    with self.status_container:
                        ui.label("⚠️ Status display error").classes("text-red-600 font-medium")
                except Exception as cascade_error:
                    import logging

                    logging.getLogger(__name__).error(
                        f"Cascading error in status display: {str(cascade_error)}", exc_info=True
                    )
                    pass  # Avoid cascading errors

    @ui.refreshable
    def _update_execution_log(self) -> None:
        """Refreshable method to update execution log"""
        self._render_execution_log()

    def _render_execution_log(self) -> None:
        """Render the execution log display"""
        try:
            if self.execution_log_container:
                self.execution_log_container.clear()

            recent_executions = FunctionExecutionService.get_recent_executions(10)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error fetching recent executions: {str(e)}", exc_info=True)
            ui.label("⚠️ Unable to load execution history").classes("text-red-600 italic")
            ui.label(f"Error: {str(e)}").classes("text-red-500 text-sm")
            return

        if not recent_executions:
            ui.label("No executions yet").classes("text-gray-500 italic")
            ui.label("Execute some functions to see their history here.").classes("text-gray-400 text-sm")
            return

        for execution in recent_executions:
            try:
                self._create_execution_log_item(execution)
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error creating execution log item: {str(e)}", exc_info=True)
                # Create a minimal error entry
                with ui.row().classes("w-full p-2 border-b border-gray-100"):
                    ui.label("⚠️ Log entry error").classes("text-red-500 text-sm")

    def _create_execution_log_item(self, execution) -> None:
        """Create a single execution log item"""
        try:
            # Status styling
            status_colors = {
                CallStatus.SUCCESS: ("text-green-600", "✅"),
                CallStatus.FAILED: ("text-red-600", "❌"),
                CallStatus.TIMEOUT: ("text-orange-600", "⏰"),
                CallStatus.RUNNING: ("text-blue-600", "⏳"),
                CallStatus.PENDING: ("text-gray-600", "⏸️"),
            }

            color_class, icon = status_colors.get(execution.status, ("text-gray-600", "❓"))

            # Format timestamp safely
            try:
                time_str = execution.started_at.strftime("%H:%M:%S") if execution.started_at else "N/A"
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error formatting timestamp: {str(e)}", exc_info=True)
                time_str = "N/A"

            # Duration display safely
            try:
                duration_display = (
                    execution.duration_display
                    if hasattr(execution, "duration_display") and execution.duration_display
                    else (f"{execution.duration_ms}ms" if execution.duration_ms else "N/A")
                )
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error formatting duration: {str(e)}", exc_info=True)
                duration_display = "N/A"

            # Function name safely
            function_name = getattr(execution, "function_name", "Unknown Function") or "Unknown Function"

            with ui.row().classes("w-full items-center justify-between p-2 border-b border-gray-100 hover:bg-gray-50"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(icon).classes("text-lg")
                    ui.label(function_name).classes("font-medium text-gray-800")
                    ui.label(time_str).classes("text-xs text-gray-500")

                with ui.row().classes("items-center gap-2"):
                    try:
                        if hasattr(execution, "response_status_code") and execution.response_status_code:
                            status_color = (
                                "text-green-600" if 200 <= execution.response_status_code < 300 else "text-red-600"
                            )
                            ui.label(str(execution.response_status_code)).classes(f"text-xs {status_color} font-mono")
                    except Exception as e:
                        import logging

                        logging.getLogger(__name__).error(f"Error displaying status code: {str(e)}", exc_info=True)
                        pass  # Skip status code if there's an error

                    ui.label(duration_display).classes("text-xs text-gray-500 font-mono")

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error creating execution log item: {str(e)}", exc_info=True)
            # Create a minimal fallback entry
            with ui.row().classes("w-full p-2 border-b border-gray-100"):
                ui.label("❓ Execution entry").classes("text-gray-500")
                ui.label("Display error").classes("text-red-500 text-xs")

    def _refresh_dashboard(self) -> None:
        """Refresh the dashboard components"""
        try:
            if hasattr(self._create_function_buttons, "refresh"):
                self._create_function_buttons.refresh()
            else:
                self._render_function_buttons()

            if hasattr(self._update_execution_log, "refresh"):
                self._update_execution_log.refresh()
            else:
                self._render_execution_log()

            self._update_status_display()
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error refreshing dashboard: {str(e)}", exc_info=True)

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
        # Immediate visibility indicator to confirm page loading
        init_label = (
            ui.label("Function Trigger Dashboard - Initializing...")
            .classes("text-2xl font-bold text-blue-600 text-center w-full p-4")
            .mark("dashboard-init")
        )

        # Root error message label - hidden by default
        error_message_label = ui.label().classes("text-red-700 font-bold p-4 bg-red-100 rounded hidden")

        try:
            # Create dashboard
            dashboard.create()

            # Remove the initialization message after successful dashboard creation
            init_label.delete()

            # Auto-refresh execution log every 10 seconds
            ui.timer(10.0, dashboard._update_execution_log.refresh)
            ui.timer(5.0, dashboard._update_status_display)

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Critical error in dashboard creation: {str(e)}", exc_info=True)

            # Show error in the root error message label
            error_message_label.set_text(f"⚠️ Dashboard Loading Error: {str(e)}")
            error_message_label.classes(remove="hidden")

            # Also remove the initialization message
            init_label.delete()

            # Add a retry button
            ui.button(
                "Retry",
                icon="refresh",
                on_click=lambda: ui.navigate.to("/"),
            ).classes("bg-red-600 text-white px-4 py-2 rounded mt-4")
