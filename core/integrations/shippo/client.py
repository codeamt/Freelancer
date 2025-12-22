"""
Shippo API Client Integration

This module provides a client for interacting with the Shippo API
for shipping, tracking, and logistics management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import httpx
from core.utils.logger import get_logger

logger = get_logger(__name__)


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
    state: Optional[str] = None
    zip: str
    country: str
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
    id: str
    rates: List[Dict]
    address_from: Dict
    address_to: Dict
    parcels: List[Dict]
    status: str
    created_at: datetime


@dataclass
class Rate:
    """Shipping rate"""
    id: str
    amount: str
    currency: str
    provider: str
    servicelevel: Dict
    estimated_days: Optional[int] = None
    duration_terms: Optional[str] = None


@dataclass
class Transaction:
    """Shipping transaction"""
    id: str
    rate: Dict
    label_url: str
    tracking_number: str
    tracking_url_provider: str
    status: str


@dataclass
class TrackingStatus:
    """Package tracking status"""
    object_id: str
    status: str
    status_details: str
    status_date: datetime
    location: Optional[Dict] = None


class ShippoClient:
    """Shippo API client"""
    
    def __init__(self, config: ShippoConfig):
        self.config = config
        self.base_url = "https://api.goshippo.com" + ("/" if config.test_mode else "")
        self.headers = {
            "Authorization": f"ShippoToken {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Shippo API"""
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=data)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Shippo API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Shippo client error: {str(e)}")
                raise
    
    # Address Management
    async def create_address(self, address: Address) -> Dict:
        """Create and validate address"""
        try:
            address_data = {
                "name": address.name,
                "street1": address.street1,
                "city": address.city,
                "zip": address.zip,
                "country": address.country,
                "validate": address.validate
            }
            
            if address.street2:
                address_data["street2"] = address.street2
            if address.state:
                address_data["state"] = address.state
            if address.phone:
                address_data["phone"] = address.phone
            if address.email:
                address_data["email"] = address.email
            
            response = await self._make_request("POST", "addresses", address_data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to create address: {str(e)}")
            raise
    
    async def validate_address(self, address_id: str) -> Dict:
        """Validate existing address"""
        try:
            response = await self._make_request("GET", f"addresses/{address_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to validate address {address_id}: {str(e)}")
            raise
    
    # Shipment Management
    async def create_shipment(self, address_from: Address, address_to: Address, parcels: List[Parcel]) -> Dict:
        """Create shipment and get rates"""
        try:
            # Create from address
            from_address = await self.create_address(address_from)
            
            # Create to address
            to_address = await self.create_address(address_to)
            
            # Prepare parcel data
            parcel_data = []
            for parcel in parcels:
                parcel_dict = {
                    "length": parcel.length,
                    "width": parcel.width,
                    "height": parcel.height,
                    "distance_unit": parcel.distance_unit,
                    "weight": parcel.weight,
                    "mass_unit": parcel.mass_unit
                }
                parcel_data.append(parcel_dict)
            
            # Create shipment
            shipment_data = {
                "address_from": from_address,
                "address_to": to_address,
                "parcels": parcel_data,
                "async": False
            }
            
            response = await self._make_request("POST", "shipments", shipment_data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to create shipment: {str(e)}")
            raise
    
    async def get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        """Get shipment by ID"""
        try:
            response = await self._make_request("GET", f"shipments/{shipment_id}")
            
            return Shipment(
                id=response["object_id"],
                rates=response.get("rates", []),
                address_from=response["address_from"],
                address_to=response["address_to"],
                parcels=response["parcels"],
                status=response["object_status"],
                created_at=datetime.fromisoformat(response["object_created"])
            )
            
        except Exception as e:
            logger.error(f"Failed to get shipment {shipment_id}: {str(e)}")
            return None
    
    async def get_shipment_rates(self, shipment_id: str) -> List[Rate]:
        """Get shipping rates for shipment"""
        try:
            shipment = await self.get_shipment(shipment_id)
            if not shipment:
                return []
            
            rates = []
            for rate_data in shipment.rates:
                rate = Rate(
                    id=rate_data["object_id"],
                    amount=rate_data["amount"],
                    currency=rate_data["currency"],
                    provider=rate_data["provider"],
                    servicelevel=rate_data["servicelevel"],
                    estimated_days=rate_data.get("estimated_days"),
                    duration_terms=rate_data.get("duration_terms")
                )
                rates.append(rate)
            
            return rates
            
        except Exception as e:
            logger.error(f"Failed to get shipment rates {shipment_id}: {str(e)}")
            return []
    
    # Transaction Management
    async def create_transaction(self, rate_id: str, label_file_type: str = "PDF") -> Transaction:
        """Create shipping transaction (purchase label)"""
        try:
            transaction_data = {
                "rate": rate_id,
                "label_file_type": label_file_type,
                "async": False
            }
            
            response = await self._make_request("POST", "transactions", transaction_data)
            
            return Transaction(
                id=response["object_id"],
                rate=response["rate"],
                label_url=response["label_url"],
                tracking_number=response["tracking_number"],
                tracking_url_provider=response["tracking_url_provider"],
                status=response["object_status"]
            )
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {str(e)}")
            raise
    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        try:
            response = await self._make_request("GET", f"transactions/{transaction_id}")
            
            return Transaction(
                id=response["object_id"],
                rate=response["rate"],
                label_url=response["label_url"],
                tracking_number=response["tracking_number"],
                tracking_url_provider=response["tracking_url_provider"],
                status=response["object_status"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
            return None
    
    async def refund_transaction(self, transaction_id: str) -> bool:
        """Refund shipping label"""
        try:
            await self._make_request("POST", f"refunds", {"transaction": transaction_id})
            return True
        except Exception as e:
            logger.error(f"Failed to refund transaction {transaction_id}: {str(e)}")
            return False
    
    # Tracking
    async def create_tracking(self, carrier: str, tracking_number: str) -> TrackingStatus:
        """Create tracking for package"""
        try:
            tracking_data = {
                "carrier": carrier,
                "tracking_number": tracking_number
            }
            
            response = await self._make_request("POST", "trackings", tracking_data)
            
            return TrackingStatus(
                object_id=response["object_id"],
                status=response["tracking_status"]["status"],
                status_details=response["tracking_status"]["status_details"],
                status_date=datetime.fromisoformat(response["tracking_status"]["status_date"]),
                location=response["tracking_status"].get("location")
            )
            
        except Exception as e:
            logger.error(f"Failed to create tracking: {str(e)}")
            raise
    
    async def get_tracking(self, tracking_id: str) -> Optional[TrackingStatus]:
        """Get tracking status"""
        try:
            response = await self._make_request("GET", f"trackings/{tracking_id}")
            
            return TrackingStatus(
                object_id=response["object_id"],
                status=response["tracking_status"]["status"],
                status_details=response["tracking_status"]["status_details"],
                status_date=datetime.fromisoformat(response["tracking_status"]["status_date"]),
                location=response["tracking_status"].get("location")
            )
            
        except Exception as e:
            logger.error(f"Failed to get tracking {tracking_id}: {str(e)}")
            return None
    
    # Carrier Services
    async def get_carriers(self) -> List[Dict]:
        """Get available carriers"""
        try:
            response = await self._make_request("GET", "carriers")
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to get carriers: {str(e)}")
            return []
    
    async def get_carrier_accounts(self) -> List[Dict]:
        """Get configured carrier accounts"""
        try:
            response = await self._make_request("GET", "carrier_accounts")
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to get carrier accounts: {str(e)}")
            return []
    
    # Manifests
    async def create_manifest(self, address: Address, transactions: List[str], shipment_date: Optional[datetime] = None) -> Dict:
        """Create shipping manifest"""
        try:
            manifest_data = {
                "address_from": {
                    "name": address.name,
                    "street1": address.street1,
                    "city": address.city,
                    "zip": address.zip,
                    "country": address.country
                },
                "transactions": transactions,
                "async": False
            }
            
            if address.state:
                manifest_data["address_from"]["state"] = address.state
            if address.street2:
                manifest_data["address_from"]["street2"] = address.street2
            
            if shipment_date:
                manifest_data["shipment_date"] = shipment_date.isoformat()
            
            response = await self._make_request("POST", "manifests", manifest_data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to create manifest: {str(e)}")
            raise
    
    # Orders
    async def create_order(self, order_data: Dict) -> Dict:
        """Create order"""
        try:
            response = await self._make_request("POST", "orders", order_data)
            return response
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise
    
    async def get_orders(self, page: int = 1, results_per_page: int = 25) -> List[Dict]:
        """Get orders"""
        try:
            params = {
                "page": page,
                "results": results_per_page
            }
            response = await self._make_request("GET", "orders", params)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to get orders: {str(e)}")
            return []
    
    # Health Check
    async def ping(self) -> bool:
        """Test API connection"""
        try:
            await self._make_request("GET", "shipments")
            return True
        except Exception as e:
            logger.error(f"Shippo API ping failed: {str(e)}")
            return False
