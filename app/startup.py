from app.database import create_tables
from app.services import seed_sample_data
import app.function_dashboard
import app.function_config
import app.execution_details
import app.execution_history


def startup() -> None:
    from nicegui import ui

    # Initialize database and sample data
    try:
        create_tables()
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Failed to create database tables: {e}", exc_info=True)
        ui.notify(f"Database initialization failed: {str(e)}", type="negative")
        raise  # Re-raise to prevent app from starting with broken database

    # Seed sample data if no configurations exist
    try:
        seed_sample_data()
    except Exception as e:
        # Sample data already exists or other error, continue
        # Log the error for observability but don't fail startup
        import logging

        logging.getLogger(__name__).info(f"Sample data seeding skipped: {e}")
        ui.notify(f"Sample data seeding: {str(e)}", type="info")

    # Register all UI modules
    app.function_dashboard.create()
    app.function_config.create()
    app.execution_details.create()
    app.execution_history.create()
