import sys
import pytest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database.connection import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
