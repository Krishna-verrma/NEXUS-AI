import pytest
import sys
from pathlib import Path
from fastapi import HTTPException

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.security import sanitize_filename, validate_file_extension, validate_file_size, safe_file_path
from app.core.config import UPLOAD_DIR

def test_sanitize_filename_traversal():
    bad_name = "../../../etc/passwd"
    clean = sanitize_filename(bad_name)
    assert "/" not in clean
    assert ".." not in clean
    assert clean == "passwd"

def test_validate_file_extension_allowed():
    assert validate_file_extension("dataset.csv") == "csv"
    assert validate_file_extension("document.pdf") == "pdf"
    assert validate_file_extension("data.json") == "json"

def test_validate_file_extension_rejected():
    with pytest.raises(HTTPException):
        validate_file_extension("exploit.exe")
    with pytest.raises(HTTPException):
        validate_file_extension("script.bat")

def test_validate_file_size():
    validate_file_size(1024 * 1024)  # 1 MB should pass
    with pytest.raises(HTTPException):
        validate_file_size(30 * 1024 * 1024)  # 30 MB should fail

def test_safe_file_path():
    p = safe_file_path(UPLOAD_DIR, "normal_file.csv")
    assert str(p).startswith(str(UPLOAD_DIR.resolve()))
