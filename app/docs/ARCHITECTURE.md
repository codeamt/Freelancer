# FastApp Architecture

**Date:** December 2, 2025  
**Version:** 2.0 (Infrastructure/Domain Separation)

---

## 🏗️ Overview

FastApp uses a **layered architecture** with clear separation between:
- **Core** - Essential framework features
- **Infrastructure Add-ons** - Reusable technical services
- **Domain Add-ons** - Business-specific features
- **Examples** - Complete demo applications

---

## 📁 Directory Structure

```
app/
├── core/                      # Core Framework
│   ├── db/                    # Database services
│   ├── middleware/            # Security, sessions, etc.
│   ├── routes/                # Main landing pages
│   ├── services/              # Core services (DB, Auth, Search, AI, Web3)
│   ├── ui/                    # UI components & layout
│   └── utils/                 # Utilities (logger, security)
│
├── add_ons/                   # Modular Add-ons
│   ├── auth/                  # 🔧 Infrastructure: Authentication
│   ├── graphql/               # 🔧 Infrastructure: GraphQL API
│   ├── media/                 # 🔧 Infrastructure: Media handling
│   ├── webhooks/              # 🔧 Infrastructure: Webhooks
│   ├── services/              # 🔧 Infrastructure: Shared services
│   │
│   └── domains/               # 🎯 Domain Features
│       ├── commerce/          # E-commerce
│       ├── lms/               # Learning Management
│       ├── social/            # Social Networking
│       └── stream/            # Streaming Platform
│
├── examples/                  # Demo Applications
│   ├── eshop/                 # E-commerce demo
│   ├── lms/                   # LMS demo
│   ├── social/                # Social network demo
│   └── streaming/             # Streaming platform demo
│
├── docs/                      # Documentation
└── tests/                     # Test suite
```

---

## 🎯 Layer Responsibilities

### **1. Core Layer**

**Purpose:** Essential framework features used by everything

**Contains:**
- Database connection & services
- Authentication service (base)
- Middleware (security, sessions)
- Search service
- AI service (HuggingFace)
- Web3 service (blockchain)
- UI layout & components
- Logging & utilities

**Rules:**
- ✅ No business logic
- ✅ No domain-specific code
- ✅ Reusable across all projects
- ✅ Minimal dependencies

**Example:**
```python
from core.services.db import DBService
from core.services.auth import AuthService
from core.middleware import apply_security
```

---

### **2. Infrastructure Add-ons**

**Purpose:** Technical services used across multiple domains

**Location:** `add_ons/` (root level)

**Contains:**
- **auth/** - User authentication & authorization
- **graphql/** - GraphQL API layer
- **media/** - File upload & storage (MinIO/S3)
- **webhooks/** - Webhook handling & processing
- **services/** - Shared business services

**Characteristics:**
- 🔧 Technical/infrastructure focus
- 🔧 Domain-agnostic
- 🔧 Used by multiple domain add-ons
- 🔧 Horizontal concerns

**Example:**
```python
from add_ons.auth import router_auth
from add_ons.media import MediaService
from add_ons.webhooks import WebhookHandler
```

---

### **3. Domain Add-ons**

**Purpose:** Business-specific features for vertical markets

**Location:** `add_ons/domains/`

**Contains:**
- **commerce/** - E-commerce (products, cart, orders)
- **lms/** - Learning Management (courses, enrollments)
- **social/** - Social Networking (posts, comments, likes)
- **stream/** - Streaming (videos, live streams, subscriptions)

**Characteristics:**
- 🎯 Business domain focus
- 🎯 Vertical-specific
- 🎯 Can be mixed & matched
- 🎯 Use infrastructure add-ons

**Example:**
```python
from add_ons.domains.commerce import router_commerce
from add_ons.domains.lms import router_lms
from add_ons.domains.social import router_social
```

---

### **4. Examples Layer**

**Purpose:** Complete demo applications showing how to use add-ons

**Location:** `examples/`

**Contains:**
- **eshop/** - E-commerce storefront
- **lms/** - Learning platform
- **social/** - Social network
- **streaming/** - Video platform

**Characteristics:**
- 📱 Complete applications
- 📱 Ready to customize
- 📱 Use core + add-ons
- 📱 Demo best practices

**Example:**
```python
# examples/eshop/app.py
from add_ons.auth import router_auth
from add_ons.domains.commerce import router_commerce

app.mount("/auth", router_auth)
app.mount("/shop", router_commerce)
```

---

## 🔄 Dependency Flow

```
┌─────────────────────────────────────────┐
│            Examples                     │
│  (eshop, lms, social, streaming)       │
└─────────────┬───────────────────────────┘
              │ uses
              ↓
┌─────────────────────────────────────────┐
│       Domain Add-ons                    │
│  (commerce, lms, social, stream)       │
└─────────────┬───────────────────────────┘
              │ uses
              ↓
┌─────────────────────────────────────────┐
│    Infrastructure Add-ons               │
│  (auth, graphql, media, webhooks)      │
└─────────────┬───────────────────────────┘
              │ uses
              ↓
┌─────────────────────────────────────────┐
│            Core                         │
│  (db, services, middleware, ui)        │
└─────────────────────────────────────────┘
```

**Rules:**
- ✅ Examples can use domains + infrastructure + core
- ✅ Domains can use infrastructure + core
- ✅ Infrastructure can use core only
- ❌ Core cannot depend on add-ons
- ❌ Lower layers cannot depend on higher layers

---

## 🎨 Design Patterns

### **1. Layered Architecture**
- Clear separation of concerns
- Each layer has specific responsibility
- Dependencies flow downward only

### **2. Plugin Architecture**
- Add-ons are pluggable
- Can be enabled/disabled per project
- Self-contained with own routes/services/UI

### **3. Domain-Driven Design**
- Domain add-ons represent business verticals
- Each domain is independent
- Domains can be combined

### **4. Composition Over Inheritance**
- Examples compose add-ons
- Add-ons compose core services
- Flexible and modular

---

## 🔧 How to Use

### **Starting a New Project**

**Option 1: Use an Example**
```bash
# Copy and customize
cp -r examples/eshop my_project/
cd my_project
# Customize as needed
```

**Option 2: Compose Add-ons**
```python
# my_app.py
from fasthtml.common import *
from add_ons.auth import router_auth
from add_ons.domains.commerce import router_commerce
from add_ons.domains.lms import router_lms

app, rt = fast_app()

# Mix domains as needed
app.mount("/auth", router_auth)
app.mount("/shop", router_commerce)
app.mount("/learn", router_lms)
```

**Option 3: Build Custom Domain**
```python
# add_ons/domains/my_domain/
from add_ons.auth import AuthService
from add_ons.media import MediaService
from core.services.db import DBService

# Build your custom domain using infrastructure
```

---

## 📊 Add-on Categories

### **Infrastructure Add-ons** (Horizontal)

| Add-on | Purpose | Used By |
|--------|---------|---------|
| **auth** | Authentication & authorization | All domains |
| **graphql** | GraphQL API layer | Search, recommendations |
| **media** | File upload & storage | Commerce, Social, Stream |
| **webhooks** | Webhook handling | Payment, notifications |
| **services** | Shared business logic | All domains |

### **Domain Add-ons** (Vertical)

| Domain | Purpose | Infrastructure Used |
|--------|---------|---------------------|
| **commerce** | E-commerce features | auth, media, webhooks |
| **lms** | Learning platform | auth, media |
| **social** | Social networking | auth, media |
| **stream** | Video streaming | auth, media |

---

## 🚀 Benefits of This Architecture

### **1. Modularity**
- ✅ Add-ons are independent
- ✅ Can be enabled/disabled
- ✅ Easy to test in isolation

### **2. Reusability**
- ✅ Infrastructure used by multiple domains
- ✅ Domains can be reused across projects
- ✅ Examples serve as templates

### **3. Scalability**
- ✅ Add new domains without affecting others
- ✅ Upgrade infrastructure independently
- ✅ Clear boundaries for team ownership

### **4. Maintainability**
- ✅ Clear separation of concerns
- ✅ Easy to locate code
- ✅ Reduced coupling

### **5. Flexibility**
- ✅ Mix and match domains
- ✅ Customize per project
- ✅ Gradual adoption

---

## 🎯 When to Create New Add-ons

### **Create Infrastructure Add-on When:**
- ✅ Feature is technical/infrastructure
- ✅ Used by multiple domains
- ✅ Horizontal concern (auth, storage, etc.)
- ✅ Domain-agnostic

**Example:** Payment processing, email service, caching

### **Create Domain Add-on When:**
- ✅ Feature is business-specific
- ✅ Represents a vertical market
- ✅ Has its own data models
- ✅ Can stand alone

**Example:** Healthcare, real estate, booking system

### **Create Example When:**
- ✅ Demonstrating add-on usage
- ✅ Providing project template
- ✅ Showing best practices
- ✅ Complete application

**Example:** Marketplace, blog, portfolio

---

## 📝 Naming Conventions

### **Infrastructure Add-ons:**
```
add_ons/
├── auth/           # Noun (what it is)
├── graphql/        # Technology name
├── media/          # Noun (what it handles)
└── webhooks/       # Noun (what it processes)
```

### **Domain Add-ons:**
```
add_ons/domains/
├── commerce/       # Business domain
├── lms/            # Acronym (Learning Management System)
├── social/         # Business domain
└── stream/         # Business domain (streaming)
```

### **Examples:**
```
examples/
├── eshop/          # Application name
├── lms/            # Application name
├── social/         # Application name
└── streaming/      # Application name
```

---

## 🔍 Finding Code

### **"Where should I put X?"**

```
Authentication logic?        → add_ons/auth/
Database connection?         → core/db/
Product catalog?             → add_ons/domains/commerce/
Course management?           → add_ons/domains/lms/
File upload?                 → add_ons/media/
Search functionality?        → core/services/search/
GraphQL schema?              → add_ons/graphql/schemas/
Security middleware?         → core/middleware/
Demo application?            → examples/
```

---

## 🧪 Testing Strategy

### **Core Tests:**
```python
tests/
├── test_async_db_redis.py      # Database
├── test_async_auth.py          # Authentication
└── test_async_e2e.py           # End-to-end
```

### **Add-on Tests:**
```python
add_ons/auth/tests/
add_ons/domains/commerce/tests/
add_ons/domains/lms/tests/
```

### **Example Tests:**
```python
examples/eshop/tests/
examples/lms/tests/
```

---

## 📚 Related Documentation

- `CODEBASE_CLEANUP.md` - Recent cleanup work
- `MIDDLEWARE_FASTHTML_COMPATIBILITY.md` - Middleware setup
- `SCHEMA_CLEANUP.md` - Schema organization
- `SETTINGS_GUIDE.md` - Configuration
- `APP_INTEGRATION_GUIDE.md` - Integration guide

---

## ✅ Summary

### **Architecture Principles:**
1. **Layered** - Core → Infrastructure → Domains → Examples
2. **Modular** - Add-ons are independent and pluggable
3. **Composable** - Mix and match as needed
4. **Scalable** - Add new features without breaking existing

### **Key Separation:**
- **Core** = Framework essentials
- **Infrastructure** = Technical services (horizontal)
- **Domains** = Business features (vertical)
- **Examples** = Demo applications

### **Benefits:**
- ✅ Clear organization
- ✅ Easy to navigate
- ✅ Reusable components
- ✅ Flexible composition

---

**Version:** 2.0  
**Status:** ✅ Production-Ready  
**Last Updated:** December 2, 2025
