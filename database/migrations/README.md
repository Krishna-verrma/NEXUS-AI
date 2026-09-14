# Nexus AI — Database Migrations

Nexus AI uses SQLAlchemy Declarative Models with automated schema synchronization.

For production migrations with schema alteration tracking:
```bash
alembic init database/migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

The database initializes automatically on backend startup via `init_db()` in `backend/app/database/session.py`.
