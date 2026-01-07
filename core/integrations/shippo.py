"""
Shippo Integration

Flattened module containing Shippo API client and models for shipping, tracking,
and logistics management.
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ===== MODELS =====

@dataclass
class ShippoConfig:
    """Shippo configuration"""
    api_key: str
    test_mode: bool = True
    timeout: int = 30


@dataclass
class Address:
    """Shipping address"""
    name: str
    street1: str
    city: str
    zip: str
    country: str
    state: Optional[str] = None
    street2: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    validate: bool = True


@dataclass
class Parcel:
    """Package/parcel information"""
    length: float
    width: float
    height: float
    distance_unit: str  # "in" or "cm"
    weight: float
    mass_unit: str  # "oz" or "g"


@dataclass
class Shipment:
    """Shipment information"""
    address_from: Address
    address_to: Address
    parcels: List[Parcel]
    carrier_accounts: Optional[List[str]] = None
    async_shipment: Optional[bool] = None


@dataclass
class Rate:
    """Shipping rate"""
    object_id: str
    amount: str
    currency: str
    provider: str
    servicelevel: Dict[str, Any]
    estimated_days: Optional[int] = None
    duration_terms: Optional[str] = None


@dataclass
class Transaction:
    """Shipping transaction"""
    object_id: str
    rate: Rate
    tracking_status: Optional[Dict[str, Any]] = None
    tracking_url_provider: Optional[str] = None
    label_url: Optional[str] = None
    commercial_invoice_url: Optional[str] = None


@dataclass
class TrackingStatus:
    """Package tracking status"""
    object_id: str
    tracking_number: str
    carrier: str
    status: str
    status_date: Optional[datetime] = None
    status_details: Optional[str] = None
    location: Optional[Dict[str, Any]] = None


# ===== CLIENT =====

class ShippoClient:
    """Shippo API client for shipping and logistics"""
    
    def __init__(self, config: Optional[ShippoConfig] = None):
        if config is None:
            config = ShippoConfig(
                api_key=os.getenv("SHIPPO_API_KEY", ""),
                test_mode=os.getenv("SHIPPO_TEST_MODE", "true").lower() == "true"
            )
        
        self.config = config
        self.base_url = "https://api.goshippo.com" if not config.test_mode else "https://api.goshippo.com"
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"ShippoToken {config.api_key}"},
            timeout=config.timeout
        )
        
        if not config.api_key:
            logger.warning("Shippo API key not configured")
    
    def create_address(self, address: Address) -> Dict[str, Any]:
        """Create and validate an address"""
        try:
            address_data = {
                "name": address.name,
                "street1": address.street1,
                "city": address.city,
                "zip": address.zip,
                "country": address.country,
                "validate": str(address.validate).lower()
            }
            
            if address.state:
                address_data["state"] = address.state
            if address.street2:
                address_data["street2"] = address.street2
            if address.phone:
                address_data["phone"] = address.phone
            if address.email:
                address_data["email"] = address.email
            
            response = self.client.post("/addresses/", json=address_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created address: {result.get('object_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create address: {e}")
            raise
    
    def create_parcel(self, parcel: Parcel) -> Dict[str, Any]:
        """Create a parcel"""
        try:
            parcel_data = {
                "length": parcel.length,
                "width": parcel.width,
                "height": parcel.height,
                "distance_unit": parcel.distance_unit,
                "weight": parcel.weight,
                "mass_unit": parcel.mass_unit
            }
            
            response = self.client.post("/parcels/", json=parcel_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created parcel: {result.get('object_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create parcel: {e}")
            raise
    
    def create_shipment(self, shipment: Shipment) -> Dict[str, Any]:
        """Create a shipment and get rates"""
        try:
            # Create from address
            from_address = self.create_address(shipment.address_from)
            
            # Create to address
            to_address = self.create_address(shipment.address_to)
            
            # Create parcels
            parcel_objects = []
            for parcel in shipment.parcels:
                parcel_obj = self.create_parcel(parcel)
                parcel_objects.append(parcel_obj)
            
            # Create shipment
            shipment_data = {
                "address_from": from_address["object_id"],
                "address_to": to_address["object_id"],
                "parcels": [p["object_id"] for p in parcel_objects]
            }
            
            if shipment.carrier_accounts:
                shipment_data["carrier_accounts"] = shipment.carrier_accounts
            
            if shipment.async_shipment is not None:
                shipment_data["async"] = shipment.async_shipment
            
            response = self.client.post("/shipments/", json=shipment_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created shipment: {result.get('object_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create shipment: {e}")
            raise
    
    def get_rates(self, shipment_id: str) -> List[Rate]:
        """Get shipping rates for a shipment"""
        try:
            response = self.client.get(f"/shipments/{shipment_id}")
            response.raise_for_status()
            
            shipment_data = response.json()
            rates = []
            
            for rate_data in shipment_data.get("rates", []):
                rate = Rate(
                    object_id=rate_data["object_id"],
                    amount=rate_data["amount"],
                    currency=rate_data["currency"],
                    provider=rate_data["provider"],
                    servicelevel=rate_data["servicelevel"],
                    estimated_days=rate_data.get("estimated_days"),
                    duration_terms=rate_data.get("duration_terms")
                )
                rates.append(rate)
            
            logger.info(f"Retrieved {len(rates)} rates for shipment {shipment_id}")
            return rates
            
        except Exception as e:
            logger.error(f"Failed to get rates: {e}")
            raise
    
    def purchase_label(self, rate_id: str) -> Transaction:
        """Purchase a shipping label"""
        try:
            response = self.client.post(f"/rates/{rate_id}/transactions")
            response.raise_for_status()
            
            transaction_data = response.json()
            
            # Parse rate data
            rate_data = transaction_data.get("rate", {})
            rate = Rate(
                object_id=rate_data["object_id"],
                amount=rate_data["amount"],
                currency=rate_data["currency"],
                provider=rate_data["provider"],
                servicelevel=rate_data["servicelevel"],
                estimated_days=rate_data.get("estimated_days"),
                duration_terms=rate_data.get("duration_terms")
            )
            
            transaction = Transaction(
                object_id=transaction_data["object_id"],
                rate=rate,
                tracking_status=transaction_data.get("tracking_status"),
                tracking_url_provider=transaction_data.get("tracking_url_provider"),
                label_url=transaction_data.get("label_url"),
                commercial_invoice_url=transaction_data.get("commercial_invoice_url")
            )
            
            logger.info(f"Purchased label: {transaction.object_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to purchase label: {e}")
            raise
    
    def track_package(self, carrier: str, tracking_number: str) -> TrackingStatus:
        """Track a package"""
        try:
            response = self.client.get(f"/tracks/{carrier}/{tracking_number}")
            response.raise_for_status()
            
            tracking_data = response.json()
            
            status_date = None
            if tracking_data.get("status_date"):
                status_date = datetime.fromisoformat(tracking_data["status_date"].replace("Z", "+00:00"))
            
            tracking_status = TrackingStatus(
                object_id=tracking_data["object_id"],
                tracking_number=tracking_data["tracking_number"],
                carrier=tracking_data["carrier"],
                status=tracking_data["status"],
                status_date=status_date,
                status_details=tracking_data.get("status_details"),
                location=tracking_data.get("location")
            )
            
            logger.info(f"Retrieved tracking status for {tracking_number}")
            return tracking_status
            
        except Exception as e:
            logger.error(f"Failed to track package: {e}")
            raise
    
    def get_carriers(self) -> List[Dict[str, Any]]:
        """Get available carriers"""
        try:
            response = self.client.get("/carriers/")
            response.raise_for_status()
            
            carriers = response.json()
            logger.info(f"Retrieved {len(carriers)} carriers")
            return carriers
            
        except Exception as e:
            logger.error(f"Failed to get carriers: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Factory function
def create_shippo_client(config: Optional[ShippoConfig] = None) -> ShippoClient:
    """Create a Shippo client instance"""
    return ShippoClient(config)


# Convenience functions
def create_address(**kwargs) -> Dict[str, Any]:
    """Convenience function to create an address"""
    client = ShippoClient()
    try:
        address = Address(**kwargs)
        return client.create_address(address)
    finally:
        client.close()


def get_shipping_rates(shipment: Shipment) -> List[Rate]:
    """Convenience function to get shipping rates"""
    client = ShippoClient()
    try:
        shipment_data = client.create_shipment(shipment)
        return client.get_rates(shipment_data["object_id"])
    finally:
        client.close()


def track_package(carrier: str, tracking_number: str) -> TrackingStatus:
    """Convenience function to track a package"""
    client = ShippoClient()
    try:
        return client.track_package(carrier, tracking_number)
    finally:
        client.close()


__all__ = [
    # Models
    'ShippoConfig',
    'Address',
    'Parcel',
    'Shipment',
    'Rate',
    'Transaction',
    'TrackingStatus',
    
    # Client
    'ShippoClient',
    'create_shippo_client',
    
    # Convenience
    'create_address',
    'get_shipping_rates',
    'track_package',
]
