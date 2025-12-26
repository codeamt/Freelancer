"""
Emergency Recovery Script

Use this script if you lose access to your encrypted data.
"""

import os
import base64
import json
from datetime import datetime

def emergency_decrypt(encrypted_data: str, master_key: str) -> str:
    """
    Emergency decrypt data with master key
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        master_key: Your master encryption key
        
    Returns:
        Decrypted data
    """
    try:
        # Decode base64
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Import crypto libraries
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        
        # Extract key ID
        stored_key_id = encrypted_bytes[:16].decode().strip('\x00')
        iv = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=f"fastapp-{stored_key_id}".encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        padding_len = decrypted[-1]
        decrypted = decrypted[:-padding_len]
        
        return decrypted.decode()
        
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None


def main():
    """Emergency recovery tool"""
    print("="*60)
    print("EMERGENCY DECRYPTION TOOL")
    print("="*60)
    print("\nThis tool helps recover encrypted data if you lose")
    print("access to your application's key management system.")
    print("\nYou will need:")
    print("1. The encrypted data (base64 encoded)")
    print("2. Your master encryption key")
    print()
    
    # Get encrypted data
    encrypted_data = input("Enter encrypted data (base64): ").strip()
    
    # Get master key
    master_key = input("Enter master key: ").strip()
    
    # Decrypt
    result = emergency_decrypt(encrypted_data, master_key)
    
    if result:
        print("\n" + "="*60)
        print("DECRYPTION SUCCESSFUL")
        print("="*60)
        print(f"\nDecrypted data:\n{result}")
    else:
        print("\n" + "="*60)
        print("DECRYPTION FAILED")
        print("="*60)
        print("\nPlease check:")
        print("1. The encrypted data is correct")
        print("2. The master key is correct")
        print("3. No data corruption occurred")


if __name__ == "__main__":
    main()
