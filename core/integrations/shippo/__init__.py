"""
Shippo Integration

Provides Shippo API integration for shipping, tracking,
and logistics management.
"""

from .client import ShippoClient, ShippoConfig, Address, Parcel

__all__ = [
    'ShippoClient',
    'ShippoConfig',
    'Address',
    'Parcel'
]
