# FastHTML Modular Monolith - Architecture Documentation

## Overview

This is a **modular monolith** web application built with FastHTML/HTMX and MonsterUI, following Domain-Driven Design (DDD) principles. The architecture supports multiple domain add-ons (Blog, Commerce, LMS, Social, Stream) with shared core infrastructure and example applications.

## Current State (December 2025)

### Working Features
- ✅ **Core Authentication** - Login, registration, JWT tokens, multi-role access control
- ✅ **E-Shop Example** - Product catalog, cart, checkout flow, admin dashboard
- ✅ **LMS Example** - Course catalog, enrollment, lessons, instructor dashboard  
- ✅ **Web Admin Portal** - Dedicated admin login, site/theme editor access
- ✅ **Role-Based Dashboards** - Super Admin, Admin, Instructor, Shop Owner dashboards
- ✅ **Security Middleware** - Input sanitization, rate limiting, security headers
- ✅ **State System + Site Editing Workflow** - Draft/publish workflow for site components
- ✅ **Blog Domain** - Complete blog system with posts, categories, comments
- ✅ **Streaming Domain** - Full streaming platform with WebRTC, video, chat
- ✅ **Social Domain** - Enhanced social network with posts, comments, likes, follows, DMs
- ✅ **Example Applications** - Sleek social and streaming examples with UI components

### Enhanced Features
- ✅ **Multi-Role System** - Hierarchical roles with permission enforcement
- ✅ **Enhanced UI Components** - Shared components across example applications
- ✅ **Production-Ready Documentation** - Comprehensive TODOs and architecture guides
- ✅ **Modular Domain System** - Self-contained domains with models, services, routes, UI

---

## Core Architectural Principles

### 1. **Polyglot Persistence**
Multiple specialized databases for different data characteristics:
- **PostgreSQL**: Structured, relational data (users, products, orders, enrollments, posts)
- **MongoDB**: Documents, flexible schemas (reviews, media, state, social data)
- **Redis**: Caching, sessions, pub/sub, cart data
- **DuckDB**: Analytics, OLAP queries
- **MinIO**: Object storage (files, images, videos)

### 2. **FastHTML + MonsterUI**
Server-side rendering with HTMX for interactivity:
- **FastHTML**: Python-native HTML generation with async support
- **MonsterUI**: DaisyUI-based component library with theme customization
- **HTMX**: Dynamic updates without JavaScript frameworks
- **Layout Wrapper**: Consistent layout system across all applications

### 3. **Dependency Injection via app.state**
Services initialized at startup and accessed via request:
- **AuthService**: Authentication and authorization with multi-role support
- **SocialService**: Social networking features (posts, comments, likes, follows)
- **DirectMessageService**: Private messaging functionality
- **CartService**: Shopping cart management
- **DBService**: Database operations with multiple adapters
- **UserService**: User management and profiles

### 4. **Multi-Role Access Control (RBAC)**
Enhanced permission system with role hierarchy:
- **super_admin**: Global configuration, all permissions
- **admin**: Platform administration, site editing
- **instructor/course_creator**: LMS content management
- **shop_owner/merchant**: E-Shop administration
- **blog_admin/blog_author**: Blog content management
- **student/user**: Standard user access

### 5. **Domain-Driven Design**
Modular domain architecture with clear boundaries:
- **Core Framework**: Independent of domain logic
- **Domain Add-ons**: Self-contained with complete MVC architecture
- **Example Applications**: Demonstrate domain capabilities
- **Shared Components**: Reusable UI components across applications

---

## Directory Structure

```
├── app.py                         # Main application entry point
├── core/                          # Core framework (shared infrastructure)
│   ├── config/                    # Configuration & validation
│   │   ├── settings_facade.py     # Role-aware settings
│   │   └── validation.py          # Startup validation
│   ├── db/                        # Database layer
│   │   ├── adapters/              # PostgreSQL, MongoDB, Redis adapters
│   │   ├── repositories/          # Repository pattern (UserRepository, etc.)
│   │   ├── session.py             # Session management
│   │   └── transaction_manager.py # 2PC transaction coordinator
│   ├── middleware/                # Request middleware
│   │   ├── security.py            # Input sanitization, rate limiting
│   │   ├── auth_context.py        # User context injection
│   │   └── error_handler.py       # Centralized error handling
│   ├── routes/                    # Core HTTP routes
│   │   ├── auth.py                # Auth routes (/auth, /admin/login)
│   │   ├── main.py                # Home, landing pages
│   │   ├── admin_sites.py         # Site/theme editor
│   │   ├── settings.py            # Settings management
│   │   └── profile.py             # User profile
│   ├── services/                  # Business logic
│   │   ├── auth/                  # AuthService, JWT, multi-role support
│   │   ├── cart/                  # CartService
│   │   ├── settings/              # Settings management
│   │   └── admin/                 # Admin services
│   ├── ui/                        # UI layer (FastHTML + MonsterUI)
│   │   ├── components/            # Reusable components
│   │   ├── pages/                 # Page templates
│   │   ├── layout.py              # Global Layout with role-based nav
│   │   └── theme/                 # Theme system
│   ├── state/                     # State management
│   │   ├── state.py               # Immutable State container
│   │   ├── actions.py             # Action base class
│   │   └── persistence.py         # MongoDB state persistence
│   ├── workflows/                 # Workflow orchestration
│   │   ├── admin.py               # Site workflow manager
│   │   └── preview.py             # Preview/publish workflow
│   └── utils/                     # Utilities (logger, helpers, security)
│
├── add_ons/                       # Domain modules
│   ├── domains/                   # Domain add-ons
│   │   ├── blog/                  # Blog domain (posts, categories, comments)
│   │   │   ├── models/            # Blog models (Post, Category, Comment)
│   │   │   ├── repositories/      # Blog repositories
│   │   │   ├── services/          # Blog services (PostService)
│   │   │   ├── routes/            # Blog routes (/blog)
│   │   │   └── ui/                # Blog UI components
│   │   ├── commerce/              # E-commerce domain
│   │   │   ├── models/            # Commerce models (Product, Order, Payment)
│   │   │   ├── repositories/      # Commerce repositories
│   │   │   ├── services/          # Commerce services
│   │   │   ├── routes/            # Commerce routes
│   │   │   └── ui/                # Commerce UI components
│   │   ├── lms/                   # Learning Management System
│   │   │   ├── models/            # LMS models (Course, Lesson, Enrollment)
│   │   │   ├── repositories/      # LMS repositories
│   │   │   ├── services/          # LMS services
│   │   │   ├── routes/            # LMS routes
│   │   │   └── ui/                # LMS UI components
│   │   ├── social/                # Social networking domain
│   │   │   ├── models/            # Social models (Post, Comment, Like, Follow, Conversation, DirectMessage)
│   │   │   ├── repositories/      # Social repositories
│   │   │   ├── services/          # Social services (SocialService, DirectMessageService)
│   │   │   ├── routes/            # Social routes
│   │   │   └── ui/                # Social UI components
│   │   └── stream/                # Streaming domain
│   │       ├── models/            # Stream models (Stream, Session, Chat)
│   │       ├── repositories/      # Stream repositories
│   │       ├── services/          # Stream services
│   │       ├── routes/            # Stream routes
│   │       └── ui/                # Stream UI components
│   └── services/                  # Shared addon services
│       ├── event_bus_base.py      # Event bus system
│       └── graphql.py             # GraphQL service
│
└── examples/                      # Working example apps
    ├── social/                     # Enhanced social network
    │   ├── app.py                  # Social app with sleek UI
    │   ├── ui/                     # Social UI components
    │   └── __init__.py             # Social app exports
    ├── streaming/                  # Streaming platform
    │   ├── app.py                  # Streaming app
    │   ├── ui/                     # Streaming UI components
    │   └── __init__.py             # Streaming app exports
    ├── lms/                       # LMS example
    │   ├── app.py                  # LMS app
    │   └── __init__.py             # LMS app exports
    └── ui/                        # Shared UI components
        └── components.py          # Shared social/streaming components
```

---

## Key Systems

### 1. Enhanced Authentication System

**Location**: `core/services/auth/`

#### Components
- **AuthService** (`auth_service.py`) - Login, registration, JWT token management
- **RoleEnforcement** (`enforcement.py`) - Permission decorators and checking
- **Multi-Role Support** - Users can have multiple roles with hierarchy
- **JWT Provider** (`providers/jwt.py`) - Token creation with role versioning
- **Models** (`models.py`) - Pydantic models for type safety

#### User Roles (Enhanced)
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"        # Global access
    ADMIN = "admin"                    # Platform administration
    INSTRUCTOR = "instructor"          # LMS content management
    SHOP_OWNER = "shop_owner"          # E-Shop administration
    BLOG_ADMIN = "blog_admin"          # Blog administration
    BLOG_AUTHOR = "blog_author"        # Blog content creation
    STUDENT = "student"                # LMS enrollment
    USER = "user"                      # Standard access
```

#### Authentication Flow
```
1. User submits credentials → /auth/login or /admin/auth/login
2. AuthService.login() validates credentials
3. JWT token created with user_id, email, roles[], role_version
4. Token stored in httponly cookie (auth_token)
5. Subsequent requests: get_current_user_from_request() extracts user with role context
6. Role enforcement decorators check permissions based on role hierarchy
```

### 2. Social Domain Architecture

**Location**: `add_ons/domains/social/`

#### Models
- **Post** - Social posts with content, privacy, engagement metrics
- **Comment** - Threaded comments on posts
- **Like** - Post likes with user relationships
- **Follow** - User following relationships
- **Conversation** - Direct message conversations
- **DirectMessage** - Individual messages in conversations

#### Services
- **SocialService** - Post management, feed generation, engagement
- **DirectMessageService** - Private messaging, conversation management

#### UI Components
- **PostComposer** - Rich post creation interface
- **PostCard** - Individual post display with interactions
- **UserCard** - User profile cards with follow functionality
- **SocialFeed** - Algorithmic feed with posts and interactions

### 3. Streaming Domain Architecture

**Location**: `add_ons/domains/stream/`

#### Models
- **Stream** - Live stream configuration and metadata
- **Session** - Streaming sessions with participants
- **Chat** - Real-time chat messages for streams

#### Services
- **StreamingService** - Stream management, WebRTC coordination
- **ChatService** - Real-time chat functionality

#### UI Components
- **StreamingHomePage** - Main streaming platform interface
- **VideoStreamCard** - Individual stream cards with controls
- **VideoUploadCard** - Video upload and management

### 4. Enhanced UI Component System

**Location**: `core/ui/` and `examples/*/ui/`

#### Layout System
- **Layout Wrapper** - Consistent layout across all applications
- **Role-Based Navigation** - Dynamic navigation based on user roles
- **Theme System** - MonsterUI with customizable themes

#### Shared Components
- **ExampleHeader** - Standardized page headers
- **ExampleNavigation** - Tab-based navigation system
- **ExampleBackLink** - Consistent back navigation
- **PostCard/UserCard** - Reusable social components

### 5. Security Middleware

**Location**: `core/middleware/security.py`

#### Features
- **Input Sanitization** - XSS prevention, SQL injection protection
- **Rate Limiting** - Request throttling per IP and user
- **CSRF Protection** - Token-based CSRF protection
- **Security Headers** - CSP, X-Frame-Options, HSTS
- **Role-Based Access** - Permission enforcement at middleware level

#### Form Data Pattern
```python
# Try sanitized form first, fallback to raw
form = getattr(request.state, 'sanitized_form', None) or await request.form()
```

---

## Request Flow

```
HTTP Request
    ↓
Security Middleware (sanitize inputs, rate limit, role check)
    ↓
Route Handler (domain-specific or core)
    ↓
Authentication Context (user extraction, role validation)
    ↓
Service Layer (business logic, domain services)
    ↓
Database Layer (PostgreSQL/MongoDB/Redis operations)
    ↓
UI Component Rendering (FastHTML + MonsterUI)
    ↓
Layout Wrapper (consistent navigation, theming)
    ↓
HTTP Response (HTML with HTMX attributes)
```

---

## Example Applications Architecture

### Social Network Example
**Location**: `examples/social/`

#### Features
- **Enhanced Feed** - Algorithmic social feed with rich posts
- **User Profiles** - Complete profile management with verification
- **Direct Messaging** - Real-time private messaging with online status
- **Engagement System** - Likes, comments, shares, follows
- **Privacy Controls** - Public vs. followers-only content

#### Technical Implementation
- Uses `SocialService` and `DirectMessageService` from domain
- Implements shared UI components for consistency
- Layout wrapper for professional appearance
- Demo data showcasing all domain features

### Streaming Platform Example
**Location**: `examples/streaming/`

#### Features
- **Live Streaming** - WebRTC-based streaming infrastructure
- **Video Management** - Upload, catalog, and video-on-demand
- **Real-time Chat** - Live chat during streams
- **Stream Discovery** - Browse and search live streams

#### Technical Implementation
- Uses streaming domain services and UI components
- Integrates with shared layout system
- Demonstrates video processing capabilities

---

## Database Architecture

### PostgreSQL (Primary)
- **Users** - Authentication and profile data
- **Products/Orders** - E-commerce transactions
- **Enrollments** - LMS course enrollments
- **Posts/Comments** - Social network content
- **Structured Data** - All relational data with ACID compliance

### MongoDB (Document Store)
- **Social Graph** - User relationships, connections
- **Content Metadata** - Media, documents, rich content
- **Analytics Data** - User behavior, engagement metrics
- **State Data** - Application state, workflows

### Redis (Cache & Sessions)
- **User Sessions** - Authentication tokens, user context
- **Shopping Cart** - Temporary cart data
- **Real-time Data** - Chat messages, notifications
- **Cache Layer** - Frequently accessed data

---

## Development Environment

### Docker Compose Setup
**Single file for local development**: `docker-compose.yml`

**Services:**
- **PostgreSQL** (port 5432) - Primary database
- **Redis** (port 6379) - Caching and sessions
- **MongoDB** (port 27017) - Document/state storage
- **DuckDB** (optional) - Analytics container
- **MinIO** (9000/9001) - S3-compatible object storage

### Quick Start
```bash
# Start services
docker compose up -d

# Run the app with demo mode
DEMO_MODE=true uv run python app.py

# Access at http://localhost:5001
```

### Example Application URLs
```bash
# Social Network
http://localhost:5001/social-example

# Streaming Platform
http://localhost:5001/streaming-example

# LMS Example
http://localhost:5001/lms-example
```

---

## Production Readiness

### Current Capabilities
- ✅ **Multi-Database Support** - PostgreSQL, MongoDB, Redis with proper adapters
- ✅ **Security Framework** - Comprehensive security middleware and authentication
- ✅ **Modular Architecture** - Domain-driven design with clear boundaries
- ✅ **Scalable Design** - Horizontal scaling ready with connection pooling
- ✅ **Production Documentation** - Comprehensive TODOs and architecture guides

### Monitoring & Observability
- **Logging System** - Centralized logging with multiple levels
- **Error Handling** - Comprehensive exception handling and reporting
- **Performance Monitoring** - Request timing and database query tracking
- **Health Checks** - Service health monitoring and alerting

### Deployment Considerations
- **Environment Configuration** - Flexible configuration management
- **Database Migrations** - Schema versioning and migration system
- **Asset Management** - Static file serving and CDN integration
- **Backup Strategy** - Automated backup and recovery procedures

---

## Future Roadmap

### Short-term (Production Ready)
- Complete comprehensive testing suite (unit, integration, E2E)
- Implement real-time notifications system
- Add file upload and media management
- Enhance analytics and reporting capabilities

### Medium-term (Scale & Performance)
- GraphQL API layer for complex queries
- WebSocket support for live features
- Background job processing with Celery
- Microservices preparation for specific domains

### Long-term (Advanced Features)
- AI-powered content recommendations
- Advanced analytics with machine learning
- Multi-tenant architecture support
- Internationalization and localization

---

## Test Credentials

For testing admin dashboards:

| Role | Email | Password | Dashboard |
|------|-------|----------|-----------|
| Admin | `admin@freelancer.dev` | `AdminPass123!` | `/admin/dashboard` |
| Instructor | `instructor@test.com` | `Instructor123!` | `/lms-example/instructor` |
| Shop Owner | `shopowner@test.com` | `Shopowner123!` | `/eshop-example/admin` |

---

**Last Updated**: December 21, 2025
**Version**: 3.0
**Architecture**: Modular Monolith with Domain-Driven Design
**Total Components**: 300+ documented files and components
