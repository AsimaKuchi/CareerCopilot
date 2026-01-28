"""
Data Encryption Module for Sensitive User Information
Uses Fernet symmetric encryption (AES-128-CBC with HMAC)
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Get or generate encryption key
def get_encryption_key() -> bytes:
    """Get encryption key from environment or generate one."""
    key = os.environ.get('DATA_ENCRYPTION_KEY')
    
    if key:
        # Use provided key
        return key.encode() if isinstance(key, str) else key
    else:
        # Generate key from a secret + salt (deterministic for same env)
        secret = os.environ.get('EMERGENT_LLM_KEY', 'default-secret-key')
        salt = b'jobmatch-encryption-salt-v1'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key

# Initialize Fernet cipher
_fernet = None

def get_fernet() -> Fernet:
    """Get or create Fernet cipher instance."""
    global _fernet
    if _fernet is None:
        _fernet = Fernet(get_encryption_key())
    return _fernet

def encrypt_field(value: str) -> str:
    """
    Encrypt a string value.
    Returns base64-encoded encrypted string with 'ENC:' prefix.
    """
    if not value:
        return value
    
    # Don't double-encrypt
    if isinstance(value, str) and value.startswith('ENC:'):
        return value
    
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return f"ENC:{encrypted.decode('utf-8')}"
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return value  # Return original on error

def decrypt_field(value: str) -> str:
    """
    Decrypt an encrypted string value.
    Handles both encrypted (ENC: prefix) and plain text.
    """
    if not value:
        return value
    
    # Only decrypt if it has our prefix
    if not isinstance(value, str) or not value.startswith('ENC:'):
        return value
    
    try:
        fernet = get_fernet()
        encrypted_data = value[4:]  # Remove 'ENC:' prefix
        decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return value  # Return original on error

# Fields that should be encrypted
SENSITIVE_FIELDS = [
    'resume_text',
    'resume_raw', 
    'phone_number',
    'linkedin_url',
    'github_url',
    'portfolio_url',
    'address_street',
    'address_city',
    'address_state',
    'address_postal_code',
    'address_country',
]

def encrypt_sensitive_data(data: dict) -> dict:
    """Encrypt all sensitive fields in a dictionary."""
    if not data:
        return data
    
    encrypted = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in encrypted and encrypted[field]:
            encrypted[field] = encrypt_field(str(encrypted[field]))
    
    return encrypted

def decrypt_sensitive_data(data: dict) -> dict:
    """Decrypt all sensitive fields in a dictionary."""
    if not data:
        return data
    
    decrypted = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in decrypted and decrypted[field]:
            decrypted[field] = decrypt_field(decrypted[field])
    
    return decrypted
