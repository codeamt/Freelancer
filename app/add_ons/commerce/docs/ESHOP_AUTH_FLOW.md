# E-Shop Authentication Flow

## Current Implementation: Single Auth System

The e-shop example uses **one unified authentication system** for all users:
- Customers (shoppers)
- Shop owners/admins
- Instructors (for LMS)
- Students (for LMS)

### User Flow:

1. **Browse Products** (No auth required)
   - Visit `/eshop-example`
   - View all products
   - See prices and descriptions

2. **Add to Cart** (Auth required)
   - Click "Add to Cart" → Prompted to login
   - Register or login
   - After login → Redirected back to shop
   - Can now add items to cart

3. **Checkout** (Auth required)
   - View cart with items
   - Click "Proceed to Checkout"
   - Complete purchase

### Role-Based Redirects After Login:

```python
if "admin" in roles:
    redirect_url = "/admin/dashboard"  # Shop owner/admin
elif "instructor" in roles:
    redirect_url = "/lms/instructor/dashboard"  # Course creator
elif "student" in roles:
    redirect_url = "/lms/student/dashboard"  # Course taker
else:
    redirect_url = "/"  # Regular customer (default)
```

## Alternative: Separate Admin Login

If you want **separate login portals** for shop owners vs customers:

### Option 1: Separate Login Pages

```
/auth/login          → Customer login
/admin/login         → Admin/shop owner login
```

**Benefits:**
- Clear separation
- Different branding
- Can add admin-specific features (2FA, IP restrictions)

**Implementation:**
```python
@router_auth.get("/admin/login")
def admin_login_page():
    return Layout(AdminLoginPage(), title="Admin Login")

@router_auth.post("/admin/login")
async def admin_login(request: Request):
    # Same auth logic, but check for admin role
    user = await auth_service.authenticate_user(email, password)
    
    if not user or "admin" not in user.get("roles", []):
        return Div(P("Access denied. Admin privileges required."))
    
    # ... rest of login
```

### Option 2: Role-Based Registration

```python
# Customer registration (default)
/auth/register → Creates user with role: ["user"]

# Admin invitation only
/admin/invite → Admin creates account with role: ["admin", "shop_owner"]
```

**Benefits:**
- Customers can self-register
- Admins are invite-only (more secure)
- Prevents unauthorized admin access

## Recommended Approach for E-commerce

### For Small Shops (Current Implementation):
✅ **Single auth system** with role-based access
- Simple to implement
- Easy to manage
- One user database
- Role determines permissions

### For Large Marketplaces:
🔄 **Separate admin portal**
- `/shop` → Customer-facing (public)
- `/admin` → Admin dashboard (restricted)
- Different login pages
- Enhanced admin security (2FA, audit logs)

## Current E-Shop Example Features

### Public Access:
- ✅ Browse products
- ✅ View product details
- ✅ Search/filter (coming soon)

### Authenticated Users:
- ✅ Add items to cart
- ✅ View cart
- ✅ Checkout
- ✅ Order history (coming soon)
- ✅ Saved payment methods (coming soon)

### Admin/Shop Owner (Future):
- ⏳ Manage products
- ⏳ View orders
- ⏳ Customer management
- ⏳ Analytics dashboard
- ⏳ Inventory management

## Implementation Examples

### Example 1: Customer Shops, Admin Manages

```python
# Customer flow
1. Visit /eshop-example
2. Browse products (no login)
3. Click "Add to Cart" → Login prompt
4. Register as "user" role
5. Add items, checkout
6. Redirected to home page

# Admin flow
1. Visit /admin/login (separate page)
2. Login with admin credentials
3. Access /admin/products → Manage inventory
4. Access /admin/orders → View customer orders
5. Access /admin/analytics → View sales data
```

### Example 2: Multi-Vendor Marketplace

```python
# Three user types:
1. Customers (role: "user")
   - Browse all products
   - Purchase from any vendor
   
2. Vendors (role: "vendor")
   - Manage own products
   - View own sales
   - Limited admin access
   
3. Platform Admin (role: "admin")
   - Manage all vendors
   - Platform settings
   - Full access
```

## Security Considerations

### Current Implementation:
- ✅ Password hashing (bcrypt)
- ✅ JWT tokens
- ✅ Role-based access control
- ✅ Session management

### Recommended Additions:
- 🔄 Email verification
- 🔄 2FA for admins
- 🔄 Rate limiting on login
- 🔄 Audit logs for admin actions
- 🔄 IP whitelisting for admin access

## Quick Customization

### To add separate admin login:

1. Create admin login page:
```python
# app/add_ons/auth/ui/pages/admin_login.py
def AdminLoginPage():
    return Div(
        H1("Admin Portal"),
        P("Authorized personnel only"),
        # ... login form
    )
```

2. Add admin route:
```python
@router_auth.get("/admin/login")
def admin_login_page():
    return Layout(AdminLoginPage(), title="Admin Login")
```

3. Add role check:
```python
@router_auth.post("/admin/login")
async def admin_login(request: Request):
    user = await auth_service.authenticate_user(email, password)
    
    if "admin" not in user.get("roles", []):
        return Div(P("Access denied"))
    
    # ... proceed with login
```

## Questions to Consider

1. **Who can register?**
   - Everyone (customers) ✅ Current
   - Invite-only (admins)
   - Approval required (vendors)

2. **Separate login pages?**
   - Single login for all ✅ Current
   - Separate admin login
   - Separate vendor login

3. **Registration flow?**
   - Self-service ✅ Current
   - Email verification
   - Admin approval

4. **Admin access?**
   - Role-based ✅ Current
   - Separate credentials
   - 2FA required

## Your Current Setup

✅ **Single unified auth** - Simple and effective for:
- Small to medium shops
- Single shop owner
- Clear role separation
- Easy to extend

**Next Steps:**
1. Test the current flow
2. Decide if you need separate admin portal
3. Add admin product management
4. Implement order processing

---

**Current Status**: Basic auth working, ready for feature expansion!
