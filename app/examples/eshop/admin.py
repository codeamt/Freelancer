"""
E-Shop Admin Dashboard

Admin/Owner dashboard for managing inventory, shipping providers, and KPIs.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, List, Dict
from core.ui.layout import Layout


def EShopAdminDashboard(user: dict, metrics: Optional[dict] = None, demo: bool = False):
    """
    E-Shop Admin dashboard with inventory, shipping, and KPI management.
    """
    BASE = "/eshop-example"
    
    if not metrics:
        metrics = {
            "total_orders": 156,
            "revenue_today": 2450.00,
            "pending_orders": 12,
            "low_stock_items": 3,
            "total_products": 24,
            "active_customers": 89
        }
    
    content = Div(
        # Header
        Div(
            Div(
                H1("E-Shop Admin Dashboard", cls="text-3xl font-bold"),
                P(f"Welcome back, {user.get('email', 'Admin')}", cls="text-gray-600"),
                cls="flex-1"
            ),
            Div(
                A("View Store", href=f"{BASE}/", cls="btn btn-outline btn-sm mr-2"),
                A("Logout", href=f"{BASE}/logout", cls="btn btn-ghost btn-sm"),
            ),
            cls="flex justify-between items-center mb-8"
        ),
        
        # Stripe Integration Notice
        Div(
            Div(
                UkIcon("credit-card", width="20", height="20", cls="mr-2"),
                Span("Stripe payments are pre-configured. ", cls="text-sm font-semibold"),
                A("Configure API Keys →", href=f"{BASE}/admin/settings/payments", cls="link link-primary text-sm"),
                cls="flex items-center"
            ),
            cls="alert alert-info mb-6"
        ),
        
        # KPI Cards
        H2("Key Performance Indicators", cls="text-2xl font-bold mb-4"),
        Div(
            Div(
                Div(
                    UkIcon("shopping-bag", width="24", height="24", cls="text-blue-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("total_orders", 0)), cls="text-3xl font-bold"),
                P("Total Orders", cls="text-gray-600 text-sm"),
                Span("+12% from last week", cls="text-green-500 text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("dollar-sign", width="24", height="24", cls="text-green-500"),
                    cls="mb-2"
                ),
                H3(f"${metrics.get('revenue_today', 0):,.2f}", cls="text-3xl font-bold"),
                P("Revenue Today", cls="text-gray-600 text-sm"),
                Span("+8% from yesterday", cls="text-green-500 text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("clock", width="24", height="24", cls="text-orange-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("pending_orders", 0)), cls="text-3xl font-bold text-orange-600"),
                P("Pending Orders", cls="text-gray-600 text-sm"),
                A("Process Now →", href=f"{BASE}/admin/orders?status=pending", cls="link link-primary text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("alert-triangle", width="24", height="24", cls="text-red-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("low_stock_items", 0)), cls="text-3xl font-bold text-red-600"),
                P("Low Stock Items", cls="text-gray-600 text-sm"),
                A("Restock →", href=f"{BASE}/admin/inventory?filter=low_stock", cls="link link-primary text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        ),
        
        # Main Management Sections
        Div(
            # Left Column - Quick Actions
            Div(
                H2("Quick Actions", cls="text-xl font-bold mb-4"),
                Div(
                    A(
                        Div(
                            UkIcon("package", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Inventory Management", cls="font-bold"),
                                P("Add, edit, and manage products", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/admin/inventory",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("truck", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Shipping Providers", cls="font-bold"),
                                P("Configure shipping options and rates", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/admin/shipping",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("clipboard-list", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Order Management", cls="font-bold"),
                                P("View and process customer orders", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/admin/orders",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("users", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Customer Management", cls="font-bold"),
                                P("View customer data and history", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/admin/customers",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("percent", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Discounts & Coupons", cls="font-bold"),
                                P("Create and manage promotions", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/admin/discounts",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                ),
                cls="lg:w-1/2"
            ),
            
            # Right Column - Recent Orders
            Div(
                H2("Recent Orders", cls="text-xl font-bold mb-4"),
                Div(
                    # Sample orders (would be dynamic in production)
                    *[
                        Div(
                            Div(
                                Span(f"#{order['id']}", cls="font-mono font-bold"),
                                Span(order["status"], cls=f"badge badge-sm {'badge-warning' if order['status'] == 'Pending' else 'badge-success'}"),
                                cls="flex justify-between items-center mb-1"
                            ),
                            Div(
                                Span(order["customer"], cls="text-sm"),
                                Span(f"${order['total']:.2f}", cls="font-bold"),
                                cls="flex justify-between items-center"
                            ),
                            cls="p-3 border-b last:border-b-0"
                        )
                        for order in [
                            {"id": "1234", "customer": "john@example.com", "total": 129.99, "status": "Pending"},
                            {"id": "1233", "customer": "jane@example.com", "total": 89.50, "status": "Shipped"},
                            {"id": "1232", "customer": "bob@example.com", "total": 245.00, "status": "Delivered"},
                            {"id": "1231", "customer": "alice@example.com", "total": 67.25, "status": "Pending"},
                            {"id": "1230", "customer": "charlie@example.com", "total": 199.99, "status": "Shipped"},
                        ]
                    ],
                    A("View All Orders →", href=f"{BASE}/admin/orders", cls="block text-center p-3 link link-primary"),
                    cls="card bg-base-100 shadow"
                ),
                cls="lg:w-1/2"
            ),
            
            cls="flex flex-col lg:flex-row gap-8 mb-8"
        ),
        
        # Settings Section
        H2("Settings", cls="text-2xl font-bold mb-4"),
        Div(
            A(
                Div(
                    UkIcon("credit-card", width="24", height="24", cls="text-primary mb-2"),
                    H4("Payment Settings", cls="font-bold"),
                    P("Configure Stripe and payment methods", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/admin/settings/payments",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("mail", width="24", height="24", cls="text-secondary mb-2"),
                    H4("Email Templates", cls="font-bold"),
                    P("Customize order confirmation emails", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/admin/settings/emails",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("globe", width="24", height="24", cls="text-accent mb-2"),
                    H4("Store Settings", cls="font-bold"),
                    P("Store name, currency, and locale", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/admin/settings/store",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("bar-chart-2", width="24", height="24", cls="text-neutral mb-2"),
                    H4("Analytics", cls="font-bold"),
                    P("View detailed sales reports", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/admin/analytics",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Admin Dashboard | E-Shop", user=user, show_auth=True, demo=demo)


def InventoryManagementPage(user: dict, products: List[dict], demo: bool = False):
    """Inventory management page for E-Shop admin."""
    BASE = "/eshop-example"
    
    content = Div(
        # Header
        Div(
            A("← Back to Dashboard", href=f"{BASE}/admin", cls="btn btn-ghost btn-sm mb-4"),
            Div(
                H1("Inventory Management", cls="text-3xl font-bold"),
                A("+ Add Product", href=f"{BASE}/admin/inventory/new", cls="btn btn-primary"),
                cls="flex justify-between items-center"
            ),
            cls="mb-6"
        ),
        
        # Filters
        Div(
            Input(type="text", placeholder="Search products...", cls="input input-bordered w-64"),
            Select(
                Option("All Categories", value=""),
                Option("Electronics", value="electronics"),
                Option("Clothing", value="clothing"),
                Option("Accessories", value="accessories"),
                cls="select select-bordered"
            ),
            Select(
                Option("All Stock Levels", value=""),
                Option("Low Stock", value="low"),
                Option("Out of Stock", value="out"),
                Option("In Stock", value="in"),
                cls="select select-bordered"
            ),
            cls="flex gap-4 mb-6"
        ),
        
        # Products Table
        Div(
            Table(
                Thead(
                    Tr(
                        Th("Product", cls=""),
                        Th("SKU", cls=""),
                        Th("Price", cls=""),
                        Th("Stock", cls=""),
                        Th("Status", cls=""),
                        Th("Actions", cls=""),
                    )
                ),
                Tbody(
                    *[
                        Tr(
                            Td(
                                Div(
                                    Img(src=p.get("image", ""), alt=p["name"], cls="w-12 h-12 object-cover rounded mr-3"),
                                    Span(p["name"], cls="font-semibold"),
                                    cls="flex items-center"
                                )
                            ),
                            Td(p.get("sku", "N/A"), cls="font-mono text-sm"),
                            Td(f"${p['price']:.2f}"),
                            Td(
                                Span(str(p.get("stock", 0)), cls=f"font-bold {'text-red-600' if p.get('stock', 0) < 10 else ''}")
                            ),
                            Td(
                                Span("Active" if p.get("active", True) else "Inactive", 
                                     cls=f"badge {'badge-success' if p.get('active', True) else 'badge-ghost'}")
                            ),
                            Td(
                                A("Edit", href=f"{BASE}/admin/inventory/{p['id']}", cls="btn btn-ghost btn-xs mr-1"),
                                Button("Delete", cls="btn btn-ghost btn-xs text-error"),
                            ),
                        )
                        for p in products
                    ]
                ),
                cls="table table-zebra w-full"
            ),
            cls="card bg-base-100 shadow overflow-x-auto"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Inventory | E-Shop Admin", user=user, show_auth=True, demo=demo)


def ShippingProvidersPage(user: dict, demo: bool = False):
    """Shipping providers configuration page."""
    BASE = "/eshop-example"
    
    providers = [
        {"id": "usps", "name": "USPS", "enabled": True, "rates": "Calculated"},
        {"id": "fedex", "name": "FedEx", "enabled": True, "rates": "Calculated"},
        {"id": "ups", "name": "UPS", "enabled": False, "rates": "Not configured"},
        {"id": "dhl", "name": "DHL", "enabled": False, "rates": "Not configured"},
    ]
    
    content = Div(
        # Header
        Div(
            A("← Back to Dashboard", href=f"{BASE}/admin", cls="btn btn-ghost btn-sm mb-4"),
            H1("Shipping Providers", cls="text-3xl font-bold mb-2"),
            P("Configure shipping options and rates for your store", cls="text-gray-600"),
            cls="mb-6"
        ),
        
        # Providers
        Div(
            *[
                Div(
                    Div(
                        Div(
                            H3(p["name"], cls="text-xl font-bold"),
                            Span("Enabled" if p["enabled"] else "Disabled", 
                                 cls=f"badge {'badge-success' if p['enabled'] else 'badge-ghost'}"),
                            cls="flex items-center gap-2"
                        ),
                        P(f"Rates: {p['rates']}", cls="text-gray-600 text-sm"),
                        cls="flex-1"
                    ),
                    Div(
                        Input(type="checkbox", cls="toggle toggle-primary", checked=p["enabled"]),
                        A("Configure", href=f"{BASE}/admin/shipping/{p['id']}", cls="btn btn-outline btn-sm ml-4"),
                        cls="flex items-center"
                    ),
                    cls="flex justify-between items-center p-4"
                )
                for p in providers
            ],
            cls="card bg-base-100 shadow divide-y"
        ),
        
        # Shipping Zones
        H2("Shipping Zones", cls="text-2xl font-bold mt-8 mb-4"),
        Div(
            Div(
                H3("Domestic (US)", cls="font-bold"),
                P("Standard rates apply", cls="text-sm text-gray-600"),
                cls="p-4 border-b"
            ),
            Div(
                H3("International", cls="font-bold"),
                P("Custom rates required", cls="text-sm text-gray-600"),
                cls="p-4 border-b"
            ),
            A("+ Add Shipping Zone", href=f"{BASE}/admin/shipping/zones/new", cls="block p-4 text-center link link-primary"),
            cls="card bg-base-100 shadow"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Shipping | E-Shop Admin", user=user, show_auth=True, demo=demo)
