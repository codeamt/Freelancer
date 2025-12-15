from decimal import Decimal


def test_cart_add_item():
    from core.services.cart.cart_service import CartService

    svc = CartService()
    cart = svc.add_to_cart(
        cart_id="session-1",
        product_id="p1",
        name="Product",
        price=Decimal("10.00"),
        quantity=2,
    )

    assert cart.item_count == 2
    assert cart.total == Decimal("20.00")
    assert cart.is_empty is False


def test_cart_remove_item():
    from core.services.cart.cart_service import CartService
    from decimal import Decimal

    svc = CartService()
    svc.add_to_cart("c", "p1", "P1", Decimal("1.00"), 1)

    assert svc.remove_from_cart("c", "p1") is True
    cart = svc.get_cart("c")
    assert cart is not None
    assert cart.item_count == 0


def test_cart_update_quantity():
    from core.services.cart.cart_service import CartService

    svc = CartService()
    cart = svc.add_to_cart("c", "p1", "P1", Decimal("2.50"), 1)

    assert svc.update_quantity("c", "p1", 3) is True
    assert cart.items["p1"].quantity == 3


def test_cart_total_calculation():
    from core.services.cart.cart_service import CartService

    svc = CartService()
    svc.add_to_cart("c", "p1", "P1", Decimal("2.50"), 2)
    svc.add_to_cart("c", "p2", "P2", Decimal("1.25"), 4)

    cart = svc.get_cart("c")
    assert cart is not None
    assert cart.total == Decimal("10.00")
