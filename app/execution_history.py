"""
Execution history module for viewing all function executions.
"""

from nicegui import ui

from app.services import FunctionExecutionService
from app.models import CallStatus


class ExecutionHistoryView:
    """View for displaying execution history"""

    def __init__(self):
        self.execution_service = FunctionExecutionService()
        self.executions_table = None
        self.filter_status = None
        self.filter_days = None

    def create(self) -> None:
        """Create the execution history view"""

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6"):
            # Header with navigation
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Execution History").classes("text-3xl font-bold text-gray-800")
                ui.button("Back to Dashboard", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes(
                    "bg-primary text-white px-4 py-2 rounded-lg"
                )

            # Filters card
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
                ui.label("Filters").classes("text-lg font-semibold mb-4")

                with ui.row().classes("w-full gap-4 items-end"):
                    with ui.column().classes("flex-1"):
                        ui.label("Status Filter").classes("text-sm font-medium text-gray-700 mb-1")
                        self.filter_status = ui.select(
                            options={
                                "all": "All Statuses",
                                "success": "Success Only",
                                "failed": "Failed Only",
                                "timeout": "Timeout Only",
                                "running": "Running Only",
                            },
                            value="all",
                        ).classes("w-full")

                    with ui.column().classes("flex-1"):
                        ui.label("Time Range").classes("text-sm font-medium text-gray-700 mb-1")
                        self.filter_days = ui.select(
                            options={
                                1: "Last 24 hours",
                                7: "Last 7 days",
                                30: "Last 30 days",
                                365: "Last year",
                                0: "All time",
                            },
                            value=7,
                        ).classes("w-full")

                    ui.button("Apply Filters", icon="filter_list", on_click=self._refresh_table).classes(
                        "bg-accent text-white px-4 py-2 rounded-lg"
                    )

                    ui.button("Refresh", icon="refresh", on_click=self._refresh_table).classes(
                        "bg-secondary text-white px-4 py-2 rounded-lg"
                    )

            # Executions table card
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
                ui.label("Recent Executions").classes("text-lg font-semibold mb-4")
                self._create_executions_table()

    def _create_executions_table(self) -> None:
        """Create the executions table"""
        # Get recent executions
        executions = FunctionExecutionService.get_recent_executions(50)

        if not executions:
            ui.label("No executions found").classes("text-gray-500 italic text-center p-8")
            return

        # Prepare table data
        table_rows = []
        for execution in executions:
            # Status styling
            status_info = self._get_status_display(execution.status, execution.success)

            # Format duration
            duration_display = (
                f"{execution.duration_ms}ms"
                if execution.duration_ms and execution.duration_ms < 1000
                else f"{execution.duration_ms / 1000:.1f}s"
                if execution.duration_ms
                else "N/A"
            )

            table_rows.append(
                {
                    "id": execution.id,
                    "function_name": execution.function_name,
                    "status": status_info["text"],
                    "status_icon": status_info["icon"],
                    "status_class": status_info["class"],
                    "started_at": execution.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "completed_at": (
                        execution.completed_at.strftime("%Y-%m-%d %H:%M:%S") if execution.completed_at else "N/A"
                    ),
                    "duration": duration_display,
                    "response_code": execution.response_status_code or "N/A",
                    "success": execution.success,
                }
            )

        # Define table columns
        columns = [
            {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "center"},
            {"name": "function_name", "label": "Function", "field": "function_name", "sortable": True, "align": "left"},
            {"name": "started_at", "label": "Started At", "field": "started_at", "sortable": True, "align": "left"},
            {"name": "duration", "label": "Duration", "field": "duration", "sortable": True, "align": "right"},
            {
                "name": "response_code",
                "label": "Status Code",
                "field": "response_code",
                "sortable": True,
                "align": "center",
            },
            {"name": "actions", "label": "Actions", "field": "id", "sortable": False, "align": "center"},
        ]

        # Create table with custom cell rendering
        self.executions_table = ui.table(columns=columns, rows=table_rows, row_key="id").classes("w-full")

        # Add custom slots for status and actions
        with self.executions_table.add_slot("body-cell-status"):
            pass  # Custom status rendering would go here

        # Add actions slot for view details button
        with self.executions_table.add_slot("body-cell-actions"):

            def create_action_button(row_data):
                return (
                    ui.button(
                        "Details", icon="visibility", on_click=lambda: ui.navigate.to(f"/execution/{row_data['id']}")
                    )
                    .classes("text-sm px-2 py-1")
                    .props("outline size=sm")
                )

        # Style the table
        self.executions_table.props("flat bordered")

    def _get_status_display(self, status: CallStatus, success: bool) -> dict:
        """Get display information for status"""
        status_map = {
            CallStatus.SUCCESS: {"text": "Success", "icon": "✅", "class": "text-green-600"},
            CallStatus.FAILED: {"text": "Failed", "icon": "❌", "class": "text-red-600"},
            CallStatus.TIMEOUT: {"text": "Timeout", "icon": "⏰", "class": "text-orange-600"},
            CallStatus.RUNNING: {"text": "Running", "icon": "⏳", "class": "text-blue-600"},
            CallStatus.PENDING: {"text": "Pending", "icon": "⏸️", "class": "text-gray-600"},
        }

        return status_map.get(status, {"text": "Unknown", "icon": "❓", "class": "text-gray-600"})

    def _refresh_table(self) -> None:
        """Refresh the executions table with current filters"""
        # For now, just recreate the table
        # In a more advanced implementation, this would apply actual filtering
        if self.executions_table:
            # Clear and recreate table container
            pass

        ui.notify("Table refreshed", type="info")


def create() -> None:
    """Create the execution history page"""

    @ui.page("/executions")
    def executions_page():
        view = ExecutionHistoryView()
        view.create()
