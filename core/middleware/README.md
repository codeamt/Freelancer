# Core Middleware Documentation

Comprehensive middleware layer for security, sessions, and request handling.

---

## 🔄 Middleware Execution Order

The middleware stack is applied in the following order (from outermost to innermost):

### **1. Auth Context Middleware** (`auth_context.py`)
**Position**: Outermost (first to process requests)
**Purpose**: Inject user context into request state for downstream middleware and routes

**Features**:
- User authentication context injection
- Role-based access control
- Request user tracking
- Session user association

**Execution**: First in the chain, processes all incoming requests

---

### **2. Security Middleware** (`security.py`)
**Position**: Second in security stack
**Components**:
- **SecurityMiddleware**: Main security orchestrator
- **RateLimitMiddleware**: Rate limiting by IP
- **SecurityHeaders**: HTTP security headers

**Execution Order**:
1. **SecurityMiddleware** - Main security orchestrator
2. **RateLimitMiddleware** - Rate limiting (60 req/min per IP)
3. **SecurityHeaders** - HTTP security headers

**Features**:
- Input sanitization
- Rate limiting
- Security headers
- CSRF protection (disabled - needs HTMX token integration)

---

### **3. Session Management** (Conditional)
**Position**: Innermost (last to process requests)
**Priority**: Redis > Cookie fallback

**Redis Session Middleware** (`redis_session.py`)
- **When**: Redis is configured and available
- **Features**: Distributed session storage, TTL-based cleanup
- **Cookie**: `session_id`, 7-day TTL, secure in production

**Cookie Session Middleware** (`cookie_session.py`)
- **When**: Redis not available or fails
- **Features**: Local cookie-based sessions, secure in production
- **Cookie**: `session`, secure in production

---

## 📋 Current Middleware Stack

```python
app.add_middleware(AuthContextMiddleware)        # User context injection
app.add_middleware(SecurityMiddleware)            # Main security orchestrator
app.add_middleware(RateLimitMiddleware)            # Rate limiting
app.add_middleware(SecurityHeaders)                 # Security headers
# Redis or Cookie session middleware (conditional)
```

---

## 📦 Available Middlewares

### **1. Security Middlewares** (`security.py`)

#### **SecurityHeaders**
Adds security headers to all responses.

**Headers Added:**
```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer-when-downgrade
Permissions-Policy: camera=(), microphone=(), geolocation=()
Content-Security-Policy: default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'
```

**Purpose:**
- Prevents clickjacking
- Enforces HTTPS
- Blocks MIME sniffing
- Restricts permissions

---

#### **CSRFMiddleware**
Protects against Cross-Site Request Forgery attacks.

**How It Works:**
1. On GET requests: Generates and sets CSRF token cookie
2. On POST/PUT/PATCH/DELETE: Validates token from cookie matches header
3. Rotates token on every GET for security

**Usage in Forms:**
```python
# In your form
Form(
    Input(type="hidden", name="csrf_token", value=request.cookies.get("csrf_token")),
    # ... other fields
    method="POST"
)
```

**HTMX Requests:**
```javascript
// Add to HTMX config
htmx.config.getCacheBusterParam = false;
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRF-Token'] = getCookie('csrf_token');
});
```

---

#### **RateLimitMiddleware**
Token bucket rate limiting per IP address.

**Configuration:**
```python
_CAP = 60.0        # Max tokens (requests)
_WINDOW = 60.0     # Time window (seconds)
# = 60 requests per 60 seconds per IP
```

**Behavior:**
- Tracks requests per IP
- Refills tokens over time
- Returns 429 when limit exceeded
- In-memory (resets on restart)

**Customization:**
```python
# Modify in security.py
_CAP = 100.0       # Allow 100 requests
_WINDOW = 60.0     # Per 60 seconds
```

---

#### **SecurityMiddleware**
Comprehensive input sanitization and logging.

**Features:**
- ✅ Sanitizes query parameters
- ✅ Sanitizes form data
- ✅ Sanitizes path parameters
- ✅ Sanitizes headers (redacts sensitive ones)
- ✅ Logs all requests with trace IDs
- ✅ Emits CloudWatch metrics (if configured)

**Sanitization:**
- HTML injection prevention
- SQL injection prevention
- XSS attack prevention

**Metrics Emitted:**
- `SanitizedRequests` - Total requests processed
- `SuspiciousInputs` - Inputs that required sanitization
- `SanitizationFailures` - Failed sanitization attempts
- `Response4xx` - Client errors
- `Response5xx` - Server errors

**CloudWatch Setup:**
```bash
# .env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
CLOUDWATCH_LOG_GROUP=FastApp/Security
CLOUDWATCH_LOG_STREAM=middleware-events
```

---

### **2. Redis Session Middleware** (`redis_session.py`)

Persistent session storage using Redis (required for chat features).

**Features:**
- ✅ Persistent sessions across restarts
- ✅ Distributed sessions (multiple servers)
- ✅ Automatic expiration (TTL)
- ✅ Secure cookie handling
- ✅ Async Redis operations

**Configuration:**
```python
RedisSessionMiddleware(
    app=app,
    redis_url="redis://localhost:6379",
    cookie_name="session_id",
    ttl_seconds=60 * 60 * 24 * 7,  # 7 days
    cookie_secure=True,             # HTTPS only
    cookie_samesite="lax",          # CSRF protection
    cookie_domain=None,             # Optional domain
    cookie_path="/"                 # Cookie path
)
```

**Usage in Routes:**
```python
@app.get("/profile")
async def profile(request: Request):
    # Access session
    session = request.scope.get("session", {})
    user_id = session.get("user_id")
    
    # Modify session
    session["last_visit"] = datetime.now().isoformat()
    
    return {"user_id": user_id}
```

**Redis Setup:**
```bash
# Local development
docker run -d -p 6379:6379 redis:alpine

# Production
# Set REDIS_URL environment variable
REDIS_URL=redis://your-redis-host:6379
```

---

## 🔧 Application in Main App

### **Automatic Application** (`app.py`)

```python
from core.middleware import apply_security, RedisSessionMiddleware

# Apply all security middlewares
apply_security(app)

# Apply Redis session middleware (if configured)
if redis_url:
    app.add_middleware(
        RedisSessionMiddleware,
        redis_url=redis_url,
        cookie_name="session_id",
        ttl_seconds=60 * 60 * 24 * 7
    )
```

### **Middleware Order** (Applied in this order)
1. **SecurityMiddleware** - Sanitization & logging (outermost)
2. **RateLimitMiddleware** - Rate limiting
3. **CSRFMiddleware** - CSRF protection
4. **SecurityHeaders** - Security headers
5. **RedisSessionMiddleware** - Session management (if configured)

**Note:** Middleware order matters! Outer middlewares run first.

---

## 🎯 Use Cases

### **1. E-Commerce (E-Shop)**
```
✅ CSRF protection for checkout
✅ Rate limiting for API calls
✅ Input sanitization for product search
✅ Security headers for payment pages
```

### **2. Learning Management (LMS)**
```
✅ CSRF protection for course enrollment
✅ Rate limiting for quiz submissions
✅ Input sanitization for user content
✅ Session management for progress tracking
```

### **3. Social Media**
```
✅ Redis sessions for real-time chat
✅ Rate limiting for posts/comments
✅ CSRF protection for actions
✅ Input sanitization for user content
```

### **4. Streaming Platform**
```
✅ Redis sessions for live chat
✅ Rate limiting for comments
✅ CSRF protection for subscriptions
✅ Security headers for video content
```

---

## 🔒 Security Best Practices

### **1. CSRF Protection**
```python
# Always include CSRF token in forms
csrf_token = request.cookies.get("csrf_token")

Form(
    Input(type="hidden", name="csrf_token", value=csrf_token),
    # ... fields
)
```

### **2. Rate Limiting**
```python
# Adjust limits based on endpoint
# High-traffic endpoints: Increase _CAP
# Sensitive endpoints: Decrease _CAP
```

### **3. Input Sanitization**
```python
# Access sanitized data
clean_query = request.state.sanitized_query
clean_form = request.state.sanitized_form
clean_headers = request.state.sanitized_headers
```

### **4. Session Security**
```python
# Always use secure cookies in production
cookie_secure=os.getenv("ENVIRONMENT") == "production"

# Set appropriate TTL
ttl_seconds=60 * 60 * 24 * 7  # 7 days for regular sessions
ttl_seconds=60 * 60            # 1 hour for sensitive sessions
```

---

## 📊 Monitoring & Logging

### **CloudWatch Metrics**

**Namespace:** `FastApp/Security`

**Metrics:**
- `SanitizedRequests` - Total requests
- `SuspiciousInputs` - Attack attempts
- `SanitizationFailures` - Processing errors
- `Response4xx` - Client errors
- `Response5xx` - Server errors

**Dashboard Example:**
```
┌─────────────────────────────────────┐
│  SanitizedRequests: 1,234           │
│  SuspiciousInputs: 12               │
│  Response4xx: 45                    │
│  Response5xx: 2                     │
└─────────────────────────────────────┘
```

### **CloudWatch Logs**

**Log Group:** `FastApp/Security`  
**Stream:** `middleware-events`

**Log Format:**
```
2025-12-02 21:30:15 [INFO] TRACE abc123 — GET /api/products | IP: 192.168.1.1 | Agent: Mozilla/5.0
2025-12-02 21:30:15 [INFO] TRACE abc123 — Response: 200 | Suspicious Inputs: 0 | Sanitization Failures: 0
```

---

## 🧪 Testing Middlewares

### **1. Test CSRF Protection**
```python
# Should fail without token
response = client.post("/api/action", data={})
assert response.status_code == 403

# Should succeed with token
csrf_token = client.get("/").cookies.get("csrf_token")
response = client.post(
    "/api/action",
    data={},
    headers={"X-CSRF-Token": csrf_token},
    cookies={"csrf_token": csrf_token}
)
assert response.status_code == 200
```

### **2. Test Rate Limiting**
```python
# Make 61 requests (exceeds limit of 60)
for i in range(61):
    response = client.get("/api/endpoint")
    if i < 60:
        assert response.status_code == 200
    else:
        assert response.status_code == 429  # Too Many Requests
```

### **3. Test Input Sanitization**
```python
# Malicious input
response = client.get("/search?q=<script>alert('xss')</script>")
assert "<script>" not in response.text
```

### **4. Test Redis Sessions**
```python
# Set session data
response = client.post("/login", data={"username": "test"})
session_cookie = response.cookies.get("session_id")

# Verify session persists
response = client.get("/profile", cookies={"session_id": session_cookie})
assert response.status_code == 200
```

---

## 🔧 Configuration

### **Environment Variables**

```bash
# Redis (for sessions)
REDIS_URL=redis://localhost:6379

# AWS CloudWatch (optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
CLOUDWATCH_LOG_GROUP=FastApp/Security
CLOUDWATCH_LOG_STREAM=middleware-events

# Security
JWT_SECRET=your-secret-key-here
ENVIRONMENT=production  # or development
```

### **Customization**

**Rate Limit:**
```python
# In security.py
_CAP = 100.0       # Max requests
_WINDOW = 60.0     # Time window
```

**Session TTL:**
```python
# In app.py
ttl_seconds=60 * 60 * 24 * 30  # 30 days
```

**CSRF Cookie:**
```python
# In security.py
CSRF_COOKIE = "csrf_token"
COOKIE_OPTS = {
    "httponly": True,
    "secure": True,      # HTTPS only
    "samesite": "strict" # Stricter CSRF protection
}
```

---

## 🚀 Performance Considerations

### **Rate Limiting**
- In-memory (fast but resets on restart)
- Consider Redis-based rate limiting for production
- Adjust limits based on traffic patterns

### **Redis Sessions**
- Use connection pooling
- Set appropriate TTL to manage memory
- Consider Redis Cluster for high availability

### **Sanitization**
- Minimal performance impact
- Runs on every request
- Caches sanitized data in request.state

---

## 📝 Summary

### **Applied by Default:**
✅ Security headers  
✅ CSRF protection  
✅ Rate limiting  
✅ Input sanitization  
✅ Request logging  

### **Optional (Requires Configuration):**
⚙️ Redis sessions (set `REDIS_URL`)  
⚙️ CloudWatch metrics (set AWS credentials)  

### **Required For:**
- **Chat features:** Redis sessions
- **Production:** All middlewares + CloudWatch
- **Development:** Security middlewares (Redis optional)

---

**Status:** ✅ All middlewares configured and applied  
**Redis:** ⚙️ Optional (required for chat)  
**CloudWatch:** ⚙️ Optional (recommended for production)
