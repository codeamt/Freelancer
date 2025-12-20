"""
Commerce Domain - Sample Data

Shared product data that can be used by examples and demos.
In production, this would be fetched from database.
"""

# Sample products for demos and examples
SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "Low Tops",
        "description": "Example shoes curated for affiliate marketing",
        "price": 89.99,
        "image": "https://images.unsplash.com/photo-1679284392816-191b1c849f76?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["Premium quality", "Multiple sizes", "Fast shipping", "30-day returns"],
        "long_description": "Stylish low-top sneakers perfect for everyday wear. Made with premium materials and designed for comfort."
    },
    {
        "id": 2,
        "name": "Namebrand Camera",
        "description": "Example DSLR camera for photography enthusiasts",
        "price": 150.00,
        "image": "https://images.unsplash.com/photo-1507804935366-720e78633272?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Electronics",
        "features": ["High resolution", "Professional grade", "Warranty included", "Accessories bundle"],
        "long_description": "Professional DSLR camera perfect for photography enthusiasts. Capture stunning photos with ease."
    },
    {
        "id": 3,
        "name": "Writing Set",
        "description": "A personal moleskine journal and included pen for note-taking",
        "price": 19.99,
        "image": "https://images.unsplash.com/photo-1611571741792-edb58d0ceb67?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Personal",
        "features": ["Premium paper", "Includes pen", "Portable size", "Gift-ready packaging"],
        "long_description": "Premium writing set with moleskine journal and quality pen. Perfect for note-taking and journaling."
    },
    {
        "id": 4,
        "name": "Plain T-Shirt",
        "description": "High-quality branded t-shirt, ready for our logo",
        "price": 29.99,
        "image": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["100% cotton", "Multiple sizes available", "Premium quality print", "Comfortable fit"],
        "long_description": "Show your support with our premium branded t-shirt. Made from 100% soft cotton with a high-quality screen print that won't fade. Available in sizes S-XXL."
    },
    {
        "id": 5,
        "name": "Designer Tote Bag",
        "description": "Eco-friendly canvas tote bag perfect for everyday use",
        "price": 19.99,
        "image": "https://images.unsplash.com/photo-1574365569389-a10d488ca3fb?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["Eco-friendly canvas", "Spacious design", "Reinforced handles", "Reusable & durable"],
        "long_description": "Carry your essentials in style with our eco-friendly canvas tote bag. Features reinforced handles, spacious interior, and a minimalist design with our logo."
    },
    {
        "id": 6,
        "name": "Unlock Album",
        "description": "Download our free sample music album - 10 tracks included!",
        "price": 0.00,
        "image": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Digital",
        "features": ["10 tracks", "High quality MP3", "Instant download", "Free forever"],
        "long_description": "Get our free sample album featuring 10 original tracks. Perfect for discovering new music. Download instantly and enjoy!"
    }
]


def get_product_by_id(product_id: int):
    """Get product by ID"""
    return next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), None)


def get_products_by_category(category: str):
    """Get products by category"""
    return [p for p in SAMPLE_PRODUCTS if p["category"] == category]


def get_all_categories():
    """Get all unique categories"""
    return list(set(p["category"] for p in SAMPLE_PRODUCTS))
