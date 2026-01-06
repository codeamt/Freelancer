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
    },
    {
        "id": 8,
        "name": "Wireless Headphones",
        "description": "Premium noise-canceling wireless headphones",
        "price": 199.99,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Electronics",
        "features": ["Active noise cancellation", "30-hour battery", "Premium sound", "Comfortable fit"],
        "long_description": "Experience premium audio with our wireless headphones featuring active noise cancellation and superior sound quality."
    },
    {
        "id": 9,
        "name": "Yoga Mat",
        "description": "Eco-friendly non-slip yoga mat",
        "price": 34.99,
        "image": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Fitness",
        "features": ["Non-slip surface", "Eco-friendly materials", "Extra cushioning", "Lightweight"],
        "long_description": "Perfect your practice with our premium yoga mat. Non-slip surface and extra cushioning for comfort and stability."
    },
    {
        "id": 10,
        "name": "Coffee Maker",
        "description": "Programmable coffee maker with thermal carafe",
        "price": 79.99,
        "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Home",
        "features": ["Programmable", "Thermal carafe", "Auto-shutoff", "Easy to clean"],
        "long_description": "Start your day right with our programmable coffee maker. Features thermal carafe to keep coffee hot for hours."
    },
    {
        "id": 11,
        "name": "Backpack",
        "description": "Water-resistant laptop backpack with USB charging",
        "price": 59.99,
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Accessories",
        "features": ["Water-resistant", "Laptop compartment", "USB charging port", "Ergonomic design"],
        "long_description": "Stay organized and connected with our modern backpack. Features dedicated laptop compartment and USB charging port."
    },
    {
        "id": 12,
        "name": "Watch",
        "description": "Classic analog watch with leather strap",
        "price": 129.99,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Accessories",
        "features": ["Genuine leather", "Water resistant", "Precision movement", "Classic design"],
        "long_description": "Timeless elegance meets modern craftsmanship. Features genuine leather strap and precise quartz movement."
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
