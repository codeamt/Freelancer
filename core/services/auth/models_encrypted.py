"""
Enhanced User Models with Encryption Support

Extends the base user models with field encryption capabilities.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from core.services.auth.models import UserRole, UserStatus
from core.utils.security import encrypt_field, decrypt_field, EncryptedField


class EncryptedUserModel(BaseModel):
    """Base model for users with encrypted fields"""
    
    # Regular fields
    id: Optional[int] = None
    email: str
    role: UserRole = UserRole.USER
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.USER])
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Encrypted fields (stored as encrypted strings)
    _encrypted_phone: Optional[str] = Field(None, alias="phone")
    _encrypted_address: Optional[str] = Field(None, alias="address")
    _encrypted_ssn: Optional[str] = Field(None, alias="ssn")
    _encrypted_credit_card: Optional[str] = Field(None, alias="credit_card")
    _encrypted_bank_account: Optional[str] = Field(None, alias="bank_account")
    _encrypted_personal_info: Optional[str] = Field(None, alias="personal_info")
    
    class Config:
        # Allow population by field name
        allow_population_by_field_name = True
        # Use enum values
        use_enum_values = True
    
    @property
    def phone(self) -> Optional[str]:
        """Get decrypted phone number"""
        if self._encrypted_phone:
            return decrypt_field(self._encrypted_phone)
        return None
    
    @phone.setter
    def phone(self, value: Optional[str]):
        """Set encrypted phone number"""
        self._encrypted_phone = encrypt_field(value) if value else None
    
    @property
    def address(self) -> Optional[str]:
        """Get decrypted address"""
        if self._encrypted_address:
            return decrypt_field(self._encrypted_address)
        return None
    
    @address.setter
    def address(self, value: Optional[str]):
        """Set encrypted address"""
        self._encrypted_address = encrypt_field(value) if value else None
    
    @property
    def ssn(self) -> Optional[str]:
        """Get decrypted SSN"""
        if self._encrypted_ssn:
            return decrypt_field(self._encrypted_ssn)
        return None
    
    @ssn.setter
    def ssn(self, value: Optional[str]):
        """Set encrypted SSN"""
        self._encrypted_ssn = encrypt_field(value) if value else None
    
    @property
    def credit_card(self) -> Optional[str]:
        """Get decrypted credit card"""
        if self._encrypted_credit_card:
            return decrypt_field(self._encrypted_credit_card)
        return None
    
    @credit_card.setter
    def credit_card(self, value: Optional[str]):
        """Set encrypted credit card"""
        self._encrypted_credit_card = encrypt_field(value) if value else None
    
    @property
    def bank_account(self) -> Optional[str]:
        """Get decrypted bank account"""
        if self._encrypted_bank_account:
            return decrypt_field(self._encrypted_bank_account)
        return None
    
    @bank_account.setter
    def bank_account(self, value: Optional[str]):
        """Set encrypted bank account"""
        self._encrypted_bank_account = encrypt_field(value) if value else None
    
    @property
    def personal_info(self) -> Optional[Dict]:
        """Get decrypted personal info"""
        if self._encrypted_personal_info:
            return decrypt_field(self._encrypted_personal_info)
        return None
    
    @personal_info.setter
    def personal_info(self, value: Optional[Dict]):
        """Set encrypted personal info"""
        self._encrypted_personal_info = encrypt_field(value) if value else None
    
    def get_encrypted_fields(self) -> Dict[str, Any]:
        """Get all encrypted field values for storage"""
        return {
            'phone': self._encrypted_phone,
            'address': self._encrypted_address,
            'ssn': self._encrypted_ssn,
            'credit_card': self._encrypted_credit_card,
            'bank_account': self._encrypted_bank_account,
            'personal_info': self._encrypted_personal_info,
        }
    
    def set_encrypted_fields(self, encrypted_data: Dict[str, Any]):
        """Set encrypted field values from storage"""
        self._encrypted_phone = encrypted_data.get('phone')
        self._encrypted_address = encrypted_data.get('address')
        self._encrypted_ssn = encrypted_data.get('ssn')
        self._encrypted_credit_card = encrypted_data.get('credit_card')
        self._encrypted_bank_account = encrypted_data.get('bank_account')
        self._encrypted_personal_info = encrypted_data.get('personal_info')
    
    def to_dict_encrypted(self) -> Dict[str, Any]:
        """Convert to dictionary with encrypted values"""
        data = self.dict(exclude_unset=True)
        # Replace decrypted fields with encrypted ones
        encrypted = self.get_encrypted_fields()
        for field in encrypted:
            if encrypted[field] is not None:
                data[field] = encrypted[field]
        return data
    
    def to_dict_decrypted(self) -> Dict[str, Any]:
        """Convert to dictionary with decrypted values"""
        data = self.dict(exclude_unset=True)
        # Remove encrypted field prefixes
        for field in ['_encrypted_phone', '_encrypted_address', '_encrypted_ssn', 
                      '_encrypted_credit_card', '_encrypted_bank_account', '_encrypted_personal_info']:
            if field in data:
                field_name = field[11:]  # Remove '_encrypted_' prefix
                data[field_name] = getattr(self, field_name)
                del data[field]
        return data


class EncryptedUserCreate(BaseModel):
    """Model for creating users with encrypted fields"""
    
    email: str
    password: str
    role: UserRole = UserRole.USER
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.USER])
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Optional encrypted fields
    phone: Optional[str] = None
    address: Optional[str] = None
    ssn: Optional[str] = None
    credit_card: Optional[str] = None
    bank_account: Optional[str] = None
    personal_info: Optional[Dict] = None
    
    def encrypt_sensitive_fields(self) -> Dict[str, Any]:
        """Encrypt sensitive fields before storage"""
        data = self.dict(exclude_unset=True)
        sensitive_fields = ['phone', 'address', 'ssn', 'credit_card', 'bank_account', 'personal_info']
        
        for field in sensitive_fields:
            if field in data and data[field] is not None:
                data[field] = encrypt_field(data[field])
        
        return data


class EncryptedUserUpdate(BaseModel):
    """Model for updating users with encrypted fields"""
    
    role: Optional[UserRole] = None
    roles: Optional[List[UserRole]] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    # Encrypted fields
    phone: Optional[str] = None
    address: Optional[str] = None
    ssn: Optional[str] = None
    credit_card: Optional[str] = None
    bank_account: Optional[str] = None
    personal_info: Optional[Dict] = None
    
    def encrypt_sensitive_fields(self) -> Dict[str, Any]:
        """Encrypt sensitive fields before storage"""
        data = self.dict(exclude_unset=True, exclude_none=True)
        sensitive_fields = ['phone', 'address', 'ssn', 'credit_card', 'bank_account', 'personal_info']
        
        for field in sensitive_fields:
            if field in data:
                data[field] = encrypt_field(data[field])
        
        return data


# Define which fields are sensitive
SENSITIVE_USER_FIELDS = [
    'phone',
    'address', 
    'ssn',
    'credit_card',
    'bank_account',
    'personal_info'
]
