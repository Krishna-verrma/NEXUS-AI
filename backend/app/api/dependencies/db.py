from app.database.session import get_db

# Re-export for standard dependency injection
__all__ = ["get_db"]
