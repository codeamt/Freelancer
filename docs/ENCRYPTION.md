# Data Encryption System

This document describes the data encryption system implemented for protecting sensitive user data.

## Overview

The encryption system provides:
- Field-level encryption for sensitive data
- Secure key management with rotation support
- Integration with the authentication system
- Automatic encryption/decryption for defined fields

## Features

### 1. Key Management
- Master key derivation using PBKDF2
- Automatic key rotation
- Support for multiple active keys
- Secure key storage

### 2. Encrypted Fields
The following user fields are encrypted by default:
- Phone numbers
- Physical addresses
- Social Security Numbers (SSN)
- Credit card numbers
- Bank account information
- Personal information (JSON)

### 3. Encryption Algorithm
- AES-256-CBC encryption
- Random IV for each encryption
- PKCS7 padding
- Base64 encoding for storage

## Usage

### Basic Encryption/Decryption

```python
from core.services.encryption import encrypt_field, decrypt_field

# Encrypt sensitive data
encrypted = encrypt_field("sensitive data")

# Decrypt when needed
decrypted = decrypt_field(encrypted)
```

### Using Encrypted Models

```python
from core.services.auth.models_encrypted import EncryptedUserModel

# Create user with encrypted fields
user = EncryptedUserModel(
    email="user@example.com",
    role="user"
)

# Set sensitive fields (automatically encrypted)
user.phone = "555-123-4567"
user.ssn = "123-45-6789"

# Access fields (automatically decrypted)
print(user.phone)  # "555-123-4567"
```

### Using Encrypted Repository

```python
from core.db.repositories.user_repository_encrypted import EncryptedUserRepository

repo = EncryptedUserRepository()

# Create user with encrypted fields
user_data = EncryptedUserCreate(
    email="user@example.com",
    password="password",
    phone="555-123-4567",
    ssn="123-45-6789"
)

user = await repo.create_user(user_data)
```

## Configuration

### Environment Variables

```bash
# Master encryption key (REQUIRED for production)
ENCRYPTION_MASTER_KEY=your-secure-master-key-here

# Or generate one with:
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Initialization

The encryption service is automatically initialized in `core/bootstrap.py`:

```python
from core.services.encryption import initialize_encryption

# Initialize with master key from environment
initialize_encryption()
```

## Key Rotation

### Manual Rotation

```python
from core.services.encryption import get_encryption_service

service = get_encryption_service()

# Rotate to new key
new_key_id = service.key_manager.rotate_key()

# Re-encrypt existing data with new key
await user_repository.rotate_encryption(user_id)
```

### Emergency Recovery

If you lose access to encrypted data, use the emergency recovery script:

```bash
python emergency.py
```

This script allows you to decrypt data using your master key.

## Security Considerations

1. **Master Key Security**
   - Store the master key securely (environment variable, key vault)
   - never commit the master key to version control
   - Use a different master key for each environment

2. **Database Security**
   - Encrypted fields are stored as base64 strings
 personalizing
   personalizing
   - personalizing
   - personalizing
   - personalizing
   - personalizing

3. **Performance**
   - Encryption adds overhead to operations
   - Encrypt only necessary fields
   - Consider caching decrypted values

## Best Practices

1. **Field Selection**
   - Encrypt only truly sensitive data
   - Avoid encrypting fields used for searching
   - personalizing

2. **Key Management**
   - Rotate keys regularly (e.g., annually)
   - Keep old keys until all data is re-encrypted
   - Document key rotation schedule

3. **Testing**
   - Test with real data in staging
   - Verify encryption/decryption works end-to-end
   - Test key rotation procedures

## Troubleshooting

### Common Issues

1. **"Invalid key size" error**
   - Ensure master key is properly set
   - Check for encoding issues

2. **"Unable to decrypt" error**
   - Verify the master key hasn't changed
   - Check if data was encrypted with an old key

3. **Performance issues**
   - Reduce number of encrypted fields
   - Consider caching decrypted values
   - Profile encryption operations

## Migration Guide

To add encryption to existing data:

1. Run the migration to add encrypted columns
2. Use the repository's `rotate_encryption` method
3. Update application code to use encrypted models

Example migration script:

```python
# Migrate existing users
users = await user_repo.get_all_users()
for user in users:
    await user_repo.rotate_encryption(user.id)
```

## Testing

Run encryption tests:

```bash
# Run all encryption tests
uv run pytest tests/test_encryption.py -v

# Run with coverage
uv run pytest tests/test_encryption.py --cov=core.services.encryption
```
