# E-Shop & LMS Example Enhancements

## ✅ Completed - LMS Example

### Free Course Demo Lesson Viewer
- ✅ Added `/course/{course_id}/lesson/{lesson_num}` route
- ✅ Video player with embedded YouTube iframe
- ✅ Lesson description and resources
- ✅ Previous/Next lesson navigation
- ✅ "Complete Course" button on final lesson
- ✅ Free course button goes directly to lesson 1 (no enrollment required)
- ✅ Enrolled courses link to "Continue Learning" → lesson 1

**Demo Flow:**
1. Browse courses at `/lms-example`
2. Click free course "Platform Orientation"
3. Click "Start Free Course" → Goes to lesson 1
4. Watch video, download resources
5. Navigate through 5 lessons
6. Complete course

---

## 🚧 In Progress - E-Shop Example

### Current State
- ✅ Category filter added
- ✅ Cart count display in header
- ✅ Cart storage updated to use quantities: `{user_id: {product_id: quantity}}`
- ✅ "Go to Cart" button added

### Still Needed

#### 1. Update Add to Cart Function
Current code at line 335-378 needs updating:

```python
@app.post("/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int, quantity: int = 1):
    """Add product to cart with quantity"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("⚠️ Please sign in to add items to cart", cls="text-warning"),
            A("Sign In", href="/auth/login?redirect=/eshop-example", cls="btn btn-sm btn-primary mt-2"),
            cls="alert alert-warning"
        )
    
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return Div(P("❌ Product not found", cls="text-error"), cls="alert alert-error")
    
    # Add to cart with quantity
    user_id = user.get("_id")
    if user_id not in cart_storage:
        cart_storage[user_id] = {}
    
    # Update quantity (add to existing or set new)
    current_qty = cart_storage[user_id].get(product_id, 0)
    cart_storage[user_id][product_id] = current_qty + quantity
    
    logger.info(f"User {user_id} added {quantity}x product {product_id} to cart")
    
    return Div(
        Span("✓ Added to Cart", cls="badge badge-success badge-lg py-4 px-6"),
        A("View Cart", href="/eshop-example/cart", cls="btn btn-primary btn-lg ml-4"),
        cls="flex items-center"
    )
```

#### 2. Add Cart Page Route

```python
@app.get("/cart")
async def view_cart(request: Request):
    """View shopping cart"""
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/eshop-example/cart")
    
    user_cart = cart_storage.get(user.get("_id"), {})
    cart_items = []
    cart_total = 0
    
    for product_id, quantity in user_cart.items():
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if product:
            cart_items.append({
                **product,
                "quantity": quantity,
                "subtotal": product["price"] * quantity
            })
            cart_total += product["price"] * quantity
    
    content = Div(
        # Header
        Div(
            H1("🛒 Shopping Cart", cls="text-3xl font-bold mb-2"),
            A("← Continue Shopping", href="/eshop-example", cls="btn btn-ghost mb-6"),
            cls="mb-8"
        ),
        
        # Cart items or empty state
        (Div(
            # Cart items list
            Div(
                *[CartItemRow(item) for item in cart_items],
                id="cart-items",
                cls="space-y-4 mb-8"
            ),
            
            # Cart summary
            Div(
                Div(
                    H3("Order Summary", cls="text-xl font-bold mb-4"),
                    Div(
                        Span("Subtotal:", cls="text-gray-600"),
                        Span(f"${cart_total:.2f}", cls="font-semibold"),
                        cls="flex justify-between mb-2"
                    ),
                    Div(
                        Span("Tax:", cls="text-gray-600"),
                        Span("$0.00", cls="font-semibold"),
                        cls="flex justify-between mb-2"
                    ),
                    Hr(cls="my-4"),
                    Div(
                        Span("Total:", cls="text-xl font-bold"),
                        Span(f"${cart_total:.2f}", cls="text-2xl font-bold text-blue-600"),
                        cls="flex justify-between mb-6"
                    ),
                    Button(
                        UkIcon("credit-card", width="20", height="20", cls="mr-2"),
                        "Proceed to Checkout",
                        cls="btn btn-primary btn-lg w-full",
                        onclick="alert('Stripe integration would go here!')"
                    ),
                    cls="bg-base-200 p-6 rounded-lg sticky top-4"
                ),
                cls="lg:col-span-1"
            ),
            cls="grid grid-cols-1 lg:grid-cols-3 gap-8"
        ) if cart_items else Div(
            UkIcon("shopping-cart", width="64", height="64", cls="text-gray-300 mb-4"),
            H2("Your cart is empty", cls="text-2xl font-bold mb-2"),
            P("Add some products to get started!", cls="text-gray-500 mb-6"),
            A("Browse Products", href="/eshop-example", cls="btn btn-primary btn-lg"),
            cls="text-center py-16"
        ))
    )
    
    return Layout(content, title="Shopping Cart | E-Shop")
```

#### 3. Add Cart Item Row Component with Quantity Controls

```python
def CartItemRow(item: dict):
    """Cart item row with quantity controls"""
    product_id = item["id"]
    quantity = item["quantity"]
    subtotal = item["subtotal"]
    is_free = item["price"] == 0
    
    return Div(
        Div(
            # Product image
            Img(
                src=item["image"],
                alt=item["name"],
                cls="w-24 h-24 object-cover rounded-lg"
            ),
            
            # Product info
            Div(
                H3(item["name"], cls="font-semibold text-lg mb-1"),
                P(item["category"], cls="text-sm text-gray-500 mb-2"),
                Span(f"${item['price']:.2f}" if not is_free else "FREE", 
                     cls="text-blue-600 font-semibold"),
                cls="flex-1"
            ),
            
            # Quantity controls
            Div(
                Button(
                    "-",
                    cls="btn btn-sm btn-outline",
                    hx_post=f"/eshop-example/cart/update/{product_id}?quantity={quantity-1}",
                    hx_target=f"#cart-item-{product_id}",
                    hx_swap="outerHTML",
                    disabled=quantity <= 1
                ),
                Span(str(quantity), cls="mx-4 font-semibold"),
                Button(
                    "+",
                    cls="btn btn-sm btn-outline",
                    hx_post=f"/eshop-example/cart/update/{product_id}?quantity={quantity+1}",
                    hx_target=f"#cart-item-{product_id}",
                    hx_swap="outerHTML"
                ),
                cls="flex items-center"
            ),
            
            # Subtotal
            Div(
                Span(f"${subtotal:.2f}", cls="font-bold text-lg"),
                cls="text-right"
            ),
            
            # Remove button
            Button(
                UkIcon("trash", width="16", height="16"),
                cls="btn btn-sm btn-ghost btn-circle",
                hx_delete=f"/eshop-example/cart/remove/{product_id}",
                hx_target=f"#cart-item-{product_id}",
                hx_swap="outerHTML",
                hx_confirm="Remove this item from cart?"
            ),
            
            cls="flex items-center gap-4 p-4 bg-base-200 rounded-lg",
            id=f"cart-item-{product_id}"
        )
    )
```

#### 4. Add Update/Remove Cart Routes

```python
@app.post("/cart/update/{product_id}")
async def update_cart_quantity(request: Request, product_id: int, quantity: int):
    """Update product quantity in cart"""
    user = await get_current_user(request)
    if not user:
        return Div()
    
    user_id = user.get("_id")
    if quantity <= 0:
        # Remove item
        if user_id in cart_storage and product_id in cart_storage[user_id]:
            del cart_storage[user_id][product_id]
        return Div()  # Empty div to replace the item
    
    # Update quantity
    if user_id in cart_storage:
        cart_storage[user_id][product_id] = quantity
    
    # Return updated cart item
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if product:
        item = {
            **product,
            "quantity": quantity,
            "subtotal": product["price"] * quantity
        }
        return CartItemRow(item)
    
    return Div()

@app.delete("/cart/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: int):
    """Remove product from cart"""
    user = await get_current_user(request)
    if not user:
        return Div()
    
    user_id = user.get("_id")
    if user_id in cart_storage and product_id in cart_storage[user_id]:
        del cart_storage[user_id][product_id]
        logger.info(f"User {user_id} removed product {product_id} from cart")
    
    return Div()  # Empty div to replace the item
```

#### 5. Update Product Detail Page - Add Quantity Selector

Replace the "Add to Cart" button section (lines 304-324) with:

```python
# Quantity selector and add to cart
Div(
    # Quantity selector (only for paid products)
    (Div(
        Label("Quantity:", cls="font-semibold mr-3"),
        Div(
            Button("-", cls="btn btn-sm btn-outline", id=f"qty-minus-{product_id}"),
            Input(
                type="number",
                value="1",
                min="1",
                max="10",
                id=f"qty-{product_id}",
                cls="input input-sm input-bordered w-20 mx-2 text-center"
            ),
            Button("+", cls="btn btn-sm btn-outline", id=f"qty-plus-{product_id}"),
            cls="flex items-center"
        ),
        Script(f"""
            const qtyInput = document.getElementById('qty-{product_id}');
            document.getElementById('qty-minus-{product_id}').onclick = () => {{
                if (qtyInput.value > 1) qtyInput.value = parseInt(qtyInput.value) - 1;
            }};
            document.getElementById('qty-plus-{product_id}').onclick = () => {{
                if (qtyInput.value < 10) qtyInput.value = parseInt(qtyInput.value) + 1;
            }};
        """),
        cls="flex items-center mb-4"
    ) if not is_free else None),
    
    # Add to cart button
    Div(id="cart-action", cls="mb-4"),
    (Div(
        Span(f"✓ In Cart ({quantity_in_cart})", cls="badge badge-success badge-lg py-4 px-6"),
        A("View Cart", href="/eshop-example/cart", cls="btn btn-primary btn-lg ml-4"),
        cls="flex items-center"
    ) if in_cart else (
        A(
            UkIcon("download", width="20", height="20", cls="mr-2"),
            "Get Free Access",
            href="#",
            cls="btn btn-success btn-lg",
            onclick="alert('Free product downloaded!')"
        ) if is_free else Button(
            UkIcon("shopping-cart", width="20", height="20", cls="mr-2"),
            "Add to Cart",
            cls="btn btn-primary btn-lg",
            hx_post=f"/eshop-example/cart/add/{product_id}",
            hx_vals=f"js:{{quantity: document.getElementById('qty-{product_id}').value}}",
            hx_target="#cart-action",
            hx_swap="innerHTML"
        ) if user else A(
            UkIcon("lock", width="20", height="20", cls="mr-2"),
            "Sign in to purchase",
            href=f"/auth/login?redirect=/eshop-example/product/{product_id}",
            cls="btn btn-primary btn-lg"
        )
    )),
    cls="mb-6"
),
```

---

## Summary

### LMS ✅ Complete
- Free course demo with 5 lessons
- Video player, resources, navigation
- No paywall for free course

### E-Shop 🚧 Needs Implementation
1. Update `add_to_cart` to handle quantities
2. Add `/cart` route with full cart page
3. Add `CartItemRow` component with +/- controls
4. Add `update_cart_quantity` and `remove_from_cart` routes
5. Update product detail page with quantity selector
6. Free product shows "Get Free Access" (no cart needed)

**Demo Flow for E-Shop:**
1. Browse products with category filter
2. Click product → see details
3. Select quantity (for paid products)
4. Add to cart
5. View cart with quantity controls
6. Update quantities or remove items
7. See total and "Proceed to Checkout" (Stripe placeholder)

---

**Next Steps:** Implement the E-Shop cart functionality as outlined above.
