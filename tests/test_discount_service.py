"""
Tests for Discount Service - Automatic discount application logic
"""
import pytest
from unittest.mock import Mock, patch
from core.services.discount_service import DiscountService
from core.services.order.order_service import OrderService, Order, OrderStatus


class TestDiscountService:
    """Test discount service functionality."""
    
    @pytest.fixture
    def mock_order_service(self):
        """Create mock order service."""
        order_service = Mock(spec=OrderService)
        return order_service
    
    @pytest.fixture
    def discount_service(self, mock_order_service):
        """Create discount service with mock order service."""
        return DiscountService(mock_order_service)
    
    def test_subscriber_discount_priority(self, discount_service, mock_order_service):
        """Test that subscriber discount takes priority over first-time discount."""
        user_id = "user123"
        user_data = {
            "email": "test@example.com",
            "subscriber_promo_code": "SUBSCRIBER_SPECIAL20"
        }
        
        # Mock that user has existing orders (not first-time)
        mock_order_service.get_user_orders.return_value = [
            Mock(status=Mock(value='paid'))
        ]
        
        result = discount_service.get_auto_discount_for_user(user_id, user_data)
        
        assert result == "SUBSCRIBER_SPECIAL20"
        # Should NOT call order service since subscriber discount takes priority
        mock_order_service.get_user_orders.assert_not_called()
    
    def test_first_time_buyer_discount(self, discount_service, mock_order_service):
        """Test that first-time buyers get WELCOME10_FIRST discount."""
        user_id = "user123"
        user_data = {
            "email": "test@example.com"
        }
        
        # Mock that user has no paid orders (first-time buyer)
        mock_order_service.get_user_orders.return_value = []
        
        result = discount_service.get_auto_discount_for_user(user_id, user_data)
        
        assert result == DiscountService.WELCOME10_FIRST
        mock_order_service.get_user_orders.assert_called_once_with(user_id)
    
    def test_no_discount_for_returning_customer(self, discount_service, mock_order_service):
        """Test that returning customers without subscriber code get no discount."""
        user_id = "user123"
        user_data = {
            "email": "test@example.com"
        }
        
        # Mock that user has existing paid orders
        mock_order_service.get_user_orders.return_value = [
            Mock(status=Mock(value='paid'))
        ]
        
        result = discount_service.get_auto_discount_for_user(user_id, user_data)
        
        assert result is None
        mock_order_service.get_user_orders.assert_called_once_with(user_id)
    
    def test_subscriber_discount_various_locations(self, discount_service, mock_order_service):
        """Test subscriber promo code detection in various user data locations."""
        user_id = "user123"
        
        # Test direct subscriber_promo_code field
        user_data1 = {"subscriber_promo_code": "SUB_DIRECT"}
        result1 = discount_service._get_subscriber_discount(user_data1)
        assert result1 == "SUB_DIRECT"
        
        # Test nested subscription field
        user_data2 = {"subscription": {"promo_code": "SUB_NESTED"}}
        result2 = discount_service._get_subscriber_discount(user_data2)
        assert result2 == "SUB_NESTED"
        
        # Test metadata field
        user_data3 = {"metadata": {"subscriber_promo_code": "SUB_META"}}
        result3 = discount_service._get_subscriber_discount(user_data3)
        assert result3 == "SUB_META"
        
        # Test fallback to promo_code field
        user_data4 = {"promo_code": "SUB_FALLBACK"}
        result4 = discount_service._get_subscriber_discount(user_data4)
        assert result4 == "SUB_FALLBACK"
    
    def test_is_first_time_buyer_true(self, discount_service, mock_order_service):
        """Test first-time buyer detection when user has no paid orders."""
        user_id = "user123"
        
        # Mock orders with no paid orders
        mock_order_service.get_user_orders.return_value = [
            Mock(status=Mock(value='pending')),
            Mock(status=Mock(value='cancelled'))
        ]
        
        result = discount_service._is_first_time_buyer(user_id)
        
        assert result is True
        mock_order_service.get_user_orders.assert_called_once_with(user_id)
    
    def test_is_first_time_buyer_false(self, discount_service, mock_order_service):
        """Test first-time buyer detection when user has paid orders."""
        user_id = "user123"
        
        # Mock orders with at least one paid order
        mock_order_service.get_user_orders.return_value = [
            Mock(status=Mock(value='cancelled')),
            Mock(status=Mock(value='paid')),
            Mock(status=Mock(value='pending'))
        ]
        
        result = discount_service._is_first_time_buyer(user_id)
        
        assert result is False
        mock_order_service.get_user_orders.assert_called_once_with(user_id)
    
    def test_is_first_time_buyer_error_handling(self, discount_service, mock_order_service):
        """Test error handling in first-time buyer detection."""
        user_id = "user123"
        
        # Mock exception
        mock_order_service.get_user_orders.side_effect = Exception("Database error")
        
        result = discount_service._is_first_time_buyer(user_id)
        
        # Should return False (no discount) on error
        assert result is False
    
    def test_validate_discount_codes(self, discount_service):
        """Test discount code validation."""
        # Test valid codes
        assert discount_service.validate_discount_code(DiscountService.WELCOME10_FIRST) is True
        assert discount_service.validate_discount_code("SUBSCRIBER_SPECIAL") is True
        assert discount_service.validate_discount_code("SUBSCRIBER_VIP_2024") is True
        
        # Test invalid codes
        assert discount_service.validate_discount_code("INVALID_CODE") is False
        assert discount_service.validate_discount_code("") is False
        assert discount_service.validate_discount_code(None) is False
    
    def test_get_discount_info(self, discount_service):
        """Test discount information retrieval."""
        # Test welcome discount info
        welcome_info = discount_service.get_discount_info(DiscountService.WELCOME10_FIRST)
        assert welcome_info is not None
        assert welcome_info["code"] == DiscountService.WELCOME10_FIRST
        assert welcome_info["type"] == "percentage"
        assert welcome_info["value"] == 10
        assert welcome_info["first_time_only"] is True
        
        # Test subscriber discount info
        sub_info = discount_service.get_discount_info("SUBSCRIBER_SPECIAL")
        assert sub_info is not None
        assert sub_info["code"] == "SUBSCRIBER_SPECIAL"
        assert sub_info["type"] == "percentage"
        assert sub_info["value"] == 15
        assert sub_info["subscriber_only"] is True
        
        # Test invalid code
        invalid_info = discount_service.get_discount_info("INVALID")
        assert invalid_info is None
    
    def test_get_auto_discount_no_user_data(self, discount_service, mock_order_service):
        """Test discount determination with no user data."""
        user_id = "user123"
        
        result = discount_service.get_auto_discount_for_user(user_id, None)
        
        assert result is None
        # Should not call order service if no user data provided
        mock_order_service.get_user_orders.assert_not_called()
    
    def test_get_auto_discount_no_order_service(self, discount_service):
        """Test discount determination with no order service."""
        user_id = "user123"
        user_data = {"email": "test@example.com"}
        
        # Create discount service with None order service
        discount_service_no_orders = DiscountService(None)
        
        result = discount_service_no_orders.get_auto_discount_for_user(user_id, user_data)
        
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
