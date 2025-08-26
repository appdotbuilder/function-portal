from app.database import create_tables
from app.services import seed_sample_data
import app.function_dashboard
import app.function_config
import app.execution_details
import app.execution_history


def startup() -> None:
    # Initialize database and sample data
    create_tables()

    # Seed sample data if no configurations exist
    try:
        seed_sample_data()
    except Exception as e:
        # Sample data already exists or other error, continue
        # Log the error for observability but don't fail startup
        import logging

        logging.getLogger(__name__).info(f"Sample data seeding skipped: {e}")

    # Register all UI modules
    app.function_dashboard.create()
    app.function_config.create()
    app.execution_details.create()
    app.execution_history.create()
