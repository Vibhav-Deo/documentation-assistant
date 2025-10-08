from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json

class EncryptionService:
    def __init__(self):
        # Use environment variable or generate key
        self.master_key = os.getenv("ENCRYPTION_KEY")
        if not self.master_key:
            self.master_key = Fernet.generate_key().decode()
            print(f"Generated encryption key: {self.master_key}")
            print("Store this key securely in ENCRYPTION_KEY environment variable")
    
    def _derive_key(self, organization_id: str) -> bytes:
        """Derive organization-specific encryption key"""
        password = f"{self.master_key}:{organization_id}".encode()
        salt = organization_id.encode()[:16].ljust(16, b'0')  # Ensure 16 bytes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data: str, organization_id: str) -> str:
        """Encrypt data with organization-specific key"""
        key = self._derive_key(organization_id)
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, organization_id: str) -> str:
        """Decrypt data with organization-specific key"""
        key = self._derive_key(organization_id)
        f = Fernet(key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def encrypt_payload(self, payload: dict, organization_id: str) -> str:
        """Encrypt JSON payload"""
        json_str = json.dumps(payload)
        return self.encrypt_data(json_str, organization_id)
    
    def decrypt_payload(self, encrypted_payload: str, organization_id: str) -> dict:
        """Decrypt JSON payload"""
        json_str = self.decrypt_data(encrypted_payload, organization_id)
        return json.loads(json_str)

# Global encryption service
encryption_service = EncryptionService()