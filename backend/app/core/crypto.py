import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger("nexus.crypto")

class CryptoService:
    _fernet: Fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            # Derive 32-byte key from existing setting or stable machine identifier
            raw_secret = os.getenv("TOKEN_ENCRYPTION_KEY", "")
            if not raw_secret:
                raw_secret = settings.ai_api_key or "nexus-ai-secure-oauth-storage-key-2026"
            
            # SHA-256 hash gives 32 bytes, base64-encode for Fernet key
            key = base64.urlsafe_b64encode(hashlib.sha256(raw_secret.encode("utf-8")).digest())
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, text: str) -> str:
        if not text:
            return ""
        try:
            f = cls._get_fernet()
            return f.encrypt(text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return text

    @classmethod
    def decrypt(cls, cipher_text: str) -> str:
        if not cipher_text:
            return ""
        try:
            f = cls._get_fernet()
            return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            # If not encrypted or wrong key, return original
            return cipher_text

def encrypt_token(text: str) -> str:
    return CryptoService.encrypt(text)

def decrypt_token(cipher_text: str) -> str:
    return CryptoService.decrypt(cipher_text)

