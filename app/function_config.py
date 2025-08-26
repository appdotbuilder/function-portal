"""
Function configuration module for adding and managing function configurations.
"""

import json
from typing import Dict, Any
from nicegui import ui

from app.services import FunctionConfigService
from app.models import FunctionConfigCreate


class FunctionConfigForm:
    """Form for creating and editing function configurations"""

    def __init__(self):
        self.name_input = None
        self.description_input = None
        self.endpoint_input = None
        self.method_select = None
        self.headers_input = None
        self.payload_input = None
        self.timeout_input = None
        self.color_select = None
        self.order_input = None
        self.form_container = None

    def create(self) -> None:
        """Create the function configuration form UI"""

        with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
            # Header with navigation
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Configure New Function").classes("text-3xl font-bold text-gray-800")
                ui.button("Back to Dashboard", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes(
                    "bg-secondary text-white px-4 py-2 rounded-lg"
                )

            # Main form card
            with ui.card().classes("w-full p-8 shadow-lg rounded-xl"):
                self._create_form_fields()

                # Action buttons
                with ui.row().classes("w-full justify-end gap-4 mt-8 pt-6 border-t border-gray-200"):
                    ui.button("Cancel", on_click=lambda: ui.navigate.to("/"), icon="cancel").classes(
                        "px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    )

                    ui.button("Save Function", on_click=self._save_function, icon="save").classes(
                        "bg-primary text-white px-6 py-2 rounded-lg shadow hover:shadow-lg"
                    )

            # Sample configurations section
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl mt-6"):
                ui.label("Quick Start Templates").classes("text-xl font-semibold mb-4")
                self._create_sample_templates()

    def _create_form_fields(self) -> None:
        """Create the form input fields"""

        # Basic information section
        ui.label("Basic Information").classes("text-lg font-semibold text-gray-800 mb-3")

        with ui.row().classes("w-full gap-6 mb-6"):
            with ui.column().classes("flex-1"):
                ui.label("Function Name *").classes("text-sm font-medium text-gray-700 mb-1")
                self.name_input = ui.input(placeholder='e.g., "Get Weather Data"').classes("w-full")

                ui.label("Description").classes("text-sm font-medium text-gray-700 mb-1 mt-4")
                self.description_input = (
                    ui.textarea(placeholder="Describe what this function does...").classes("w-full").props("rows=2")
                )

            with ui.column().classes("flex-1"):
                ui.label("Button Color").classes("text-sm font-medium text-gray-700 mb-1")
                self.color_select = ui.select(
                    options={
                        "primary": "Blue (Primary)",
                        "secondary": "Gray (Secondary)",
                        "accent": "Green (Accent)",
                        "positive": "Success Green",
                        "negative": "Error Red",
                        "warning": "Warning Orange",
                        "info": "Info Blue",
                    },
                    value="primary",
                ).classes("w-full")

                ui.label("Display Order").classes("text-sm font-medium text-gray-700 mb-1 mt-4")
                self.order_input = ui.number(value=0, format="%d").classes("w-full")

        ui.separator().classes("my-6")

        # API configuration section
        ui.label("API Configuration").classes("text-lg font-semibold text-gray-800 mb-3")

        with ui.row().classes("w-full gap-6 mb-4"):
            with ui.column().classes("flex-2"):
                ui.label("Endpoint URL *").classes("text-sm font-medium text-gray-700 mb-1")
                self.endpoint_input = ui.input(placeholder="https://api.example.com/endpoint").classes("w-full")

            with ui.column().classes("flex-1"):
                ui.label("HTTP Method").classes("text-sm font-medium text-gray-700 mb-1")
                self.method_select = ui.select(options=["GET", "POST", "PUT", "DELETE"], value="POST").classes("w-full")

            with ui.column().classes("flex-1"):
                ui.label("Timeout (seconds)").classes("text-sm font-medium text-gray-700 mb-1")
                self.timeout_input = ui.number(value=30, min=1, max=300, format="%d").classes("w-full")

        # Advanced configuration section
        with ui.expansion("Advanced Configuration", icon="settings").classes("w-full mb-4"):
            with ui.column().classes("gap-4 p-4"):
                ui.label("HTTP Headers (JSON format)").classes("text-sm font-medium text-gray-700 mb-1")
                self.headers_input = (
                    ui.textarea(
                        placeholder='{\n  "Content-Type": "application/json",\n  "Authorization": "Bearer token"\n}',
                        value="{}",
                    )
                    .classes("w-full font-mono text-sm")
                    .props("rows=4")
                )

                ui.label("Request Payload (JSON format)").classes("text-sm font-medium text-gray-700 mb-1 mt-4")
                self.payload_input = (
                    ui.textarea(placeholder='{\n  "message": "Hello World",\n  "data": {...}\n}', value="{}")
                    .classes("w-full font-mono text-sm")
                    .props("rows=6")
                )

    def _create_sample_templates(self) -> None:
        """Create sample configuration templates"""
        templates = [
            {
                "name": "JSONPlaceholder GET",
                "description": "Fetch posts from JSONPlaceholder",
                "endpoint": "https://jsonplaceholder.typicode.com/posts",
                "method": "GET",
                "headers": {},
                "payload": {},
                "color": "info",
            },
            {
                "name": "HTTPBin POST Test",
                "description": "Test POST request to HTTPBin",
                "endpoint": "https://httpbin.org/post",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "payload": {"message": "Hello from Function Trigger!"},
                "color": "accent",
            },
            {
                "name": "Weather API",
                "description": "Get weather data (requires API key)",
                "endpoint": "https://api.openweathermap.org/data/2.5/weather",
                "method": "GET",
                "headers": {},
                "payload": {"q": "London", "appid": "YOUR_API_KEY"},
                "color": "warning",
            },
        ]

        with ui.row().classes("w-full gap-4 flex-wrap"):
            for template in templates:
                with ui.card().classes("p-4 min-w-64 border border-gray-200 hover:shadow-md cursor-pointer"):
                    ui.label(template["name"]).classes("font-semibold text-gray-800")
                    ui.label(template["description"]).classes("text-sm text-gray-600 mt-1")
                    ui.label(f"{template['method']} {template['endpoint'][:40]}...").classes(
                        "text-xs text-blue-600 font-mono mt-2"
                    )

                    ui.button("Use Template", on_click=lambda _, t=template: self._load_template(t)).classes(
                        "mt-3 text-sm px-3 py-1"
                    ).props("outline size=sm")

    def _load_template(self, template: Dict[str, Any]) -> None:
        """Load a template into the form"""
        if self.name_input:
            self.name_input.set_value(template["name"])
        if self.description_input:
            self.description_input.set_value(template["description"])
        if self.endpoint_input:
            self.endpoint_input.set_value(template["endpoint"])
        if self.method_select:
            self.method_select.set_value(template["method"])
        if self.headers_input:
            self.headers_input.set_value(json.dumps(template["headers"], indent=2))
        if self.payload_input:
            self.payload_input.set_value(json.dumps(template["payload"], indent=2))
        if self.color_select:
            self.color_select.set_value(template["color"])

        ui.notify("Template loaded! Modify as needed and save.", type="positive")

    def _save_function(self) -> None:
        """Save the function configuration"""
        try:
            # Validate required fields
            if not self.name_input or not self.name_input.value:
                ui.notify("Function name is required", type="negative")
                return

            if not self.endpoint_input or not self.endpoint_input.value:
                ui.notify("Endpoint URL is required", type="negative")
                return

            # Parse JSON fields
            headers = {}
            payload = {}

            if self.headers_input and self.headers_input.value.strip():
                try:
                    headers = json.loads(self.headers_input.value)
                    if not isinstance(headers, dict):
                        raise ValueError("Headers must be a JSON object")
                except (json.JSONDecodeError, ValueError) as e:
                    import logging

                    logging.getLogger(__name__).warning(f"Invalid headers JSON: {e}")
                    ui.notify(f"Invalid headers JSON: {str(e)}", type="negative")
                    return

            if self.payload_input and self.payload_input.value.strip():
                try:
                    payload = json.loads(self.payload_input.value)
                except json.JSONDecodeError as e:
                    import logging

                    logging.getLogger(__name__).warning(f"Invalid payload JSON: {e}")
                    ui.notify(f"Invalid payload JSON: {str(e)}", type="negative")
                    return

            # Create configuration
            # Get method value with proper type checking
            method_value = "POST"
            if self.method_select and self.method_select.value:
                method_value = str(self.method_select.value)

            config_data = FunctionConfigCreate(
                name=self.name_input.value.strip(),
                description=self.description_input.value.strip() if self.description_input else "",
                endpoint_url=self.endpoint_input.value.strip(),
                http_method=method_value,
                headers=headers,
                payload=payload,
                timeout_seconds=int(self.timeout_input.value) if self.timeout_input else 30,
                button_color=str(self.color_select.value)
                if self.color_select and self.color_select.value
                else "primary",
                display_order=int(self.order_input.value) if self.order_input else 0,
            )

            # Save to database
            FunctionConfigService.create(config_data)

            ui.notify(f'✅ Function "{config_data.name}" saved successfully!', type="positive")

            # Navigate back to dashboard after short delay
            ui.timer(1.5, lambda: ui.navigate.to("/"), once=True)

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error saving function: {e}")
            ui.notify(f"Error saving function: {str(e)}", type="negative")


def create() -> None:
    """Create the function configuration page"""

    @ui.page("/config")
    def config_page():
        form = FunctionConfigForm()
        form.create()
