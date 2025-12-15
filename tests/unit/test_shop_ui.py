def test_product_card_render():
    from app.examples.eshop.ui import ProductCard

    product = {
        "id": 1,
        "name": "Test Product",
        "description": "A great product",
        "price": 9.99,
        "category": "Test",
        "image": "https://example.com/img.png",
    }

    html = str(ProductCard(product, user={"id": 1}, base_path="/eshop-example"))

    assert "Test Product" in html
    assert "A great product" in html
    assert "$9.99" in html
    assert "href=\"/eshop-example/product/1\"" in html
