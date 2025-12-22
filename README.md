# FastApp - Modular Web Application Platform (WIP)

<p align="center">
  <img src="public/app_preview.png" alt="FastApp Platform Preview" width="60%">
</p>

A modern, modular FastHTML platform with authentication, role-based access control, and ready-to-use example applications. Built with Domain-Driven Design principles and production-ready architecture. Perfect for freelance developers building custom solutions for clients.

## 🚀 Quick Start

```bash
# Install dependencies
uv pip install -e .

# Start the application
DEMO_MODE=true uv run python app.py
```

Visit: `http://localhost:5001`

**No database required!** The app runs in demo mode with in-memory storage by default.

## ✨ Features

### 🔐 Enhanced Authentication System

- **JWT-based authentication** with bcrypt password hashing
- **Multi-role support** with hierarchical permissions (Super Admin, Admin, Instructor, Shop Owner, etc.)
- **Role-based access control** with permission enforcement decorators
- **User registration** with role selection
- **Smart redirects** - returns users to their original page after login
- **Demo mode** - works without database connection

### 🎯 Example Applications

Five fully-functional example apps showcasing different use cases:

#### 1. 🛍️ E-Shop (`/eshop-example`)

- Product catalog with search and filtering
- Shopping cart system with Redis persistence
- Complete checkout flow
- **FREE product** for testing
- Product detail pages with features
- Auth-protected cart and checkout
- Admin dashboard for shop owners

#### 2. 📚 LMS (`/lms-example`)

- Course catalog with ratings and stats
- Student enrollment system
- "My Courses" dashboard
- **FREE orientation course**
- Course detail pages with syllabus
- Progress tracking
- Instructor dashboard

#### 3. 🌐 Social Network (`/social-example`)

- **Enhanced social feed** with posts, comments, and engagement
- User profiles with followers and verification
- **Direct messaging** with real-time chat
- Post composer with rich content support
- **Sleek UI** with modern design
- Social interactions (likes, shares, follows)

#### 4. 📺 Streaming Platform (`/streaming-example`)

- **Live streaming** with WebRTC support
- Video upload and management
- **Real-time chat** during streams
- Stream discovery and browsing
- Video-on-demand capabilities
- **Professional streaming UI**

#### 5. 📝 Blog System (`/blog`)

- Complete blog functionality with posts and categories
- Comment system with threading
- **Admin interface** for content management
- SEO-friendly URLs and metadata
- **Default add-on** for production use

### 🎨 UI Components

- **MonsterUI** - Beautiful, accessible components
- **DaisyUI** - Tailwind CSS component library
- **Responsive design** - Mobile-first approach
- **Dark mode ready** - Theme support built-in
- **Shared components** across all example applications
- **Professional layouts** with consistent navigation

## 🛠️ Tech Stack

### Core

- **FastHTML** - Modern Python web framework with HTMX
- **MonsterUI** - Component library built on DaisyUI
- **Tailwind CSS** - Utility-first CSS framework
- **Python 3.13+** - Modern Python features

### Authentication & Security

- **JWT** - Token-based authentication with role versioning
- **bcrypt** - Password hashing
- **Multi-role access control** - Flexible permission system
- **Security middleware** - Input sanitization, rate limiting, CSRF protection

### Database (Production)

- **PostgreSQL** - Primary database for structured data
- **MongoDB** - Document storage for flexible schemas
- **Redis** - Caching, sessions, and pub/sub
- **DuckDB** - Analytics and OLAP queries
- **MinIO** - S3-compatible object storage

### Architecture

- **Domain-Driven Design** - Modular domain system
- **Repository Pattern** - Clean data access layer
- **Dependency Injection** - Service container with app.state
- **Modular Monolith** - Scalable monolithic architecture

## 📚 Documentation

### Core Documentation

- [Architecture](ARCHITECTURE.md) - Complete architecture overview
- [Codebase Index](CODEBASE_INDEX.md) - Quick navigation guide
- [File Manifest](FILE_MANIFEST.md) - Complete file listing
- [Production TODOs](TODOS.md) - Comprehensive roadmap
- [Admin Credentials](ADMIN_CREDENTIALS.md) - Test credentials

### Technical Guides

- [Type Safety](docs/TYPE_SAFETY.md) - Pydantic usage guide
- [Error Handling](docs/ERROR_HANDLING.md) - Error handling patterns
- [Dependency Injection](docs/DEPENDENCY_INJECTION_GUIDE.md) - DI system guide

## 🔧 Configuration

### Demo Mode (Default)

No configuration needed! Just run `DEMO_MODE=true uv run python app.py` and everything works with in-memory storage.

### Production Mode

Create a `.env` file:

```bash
# Core Configuration
ENVIRONMENT=production
DEMO_MODE=false

# Security (REQUIRED for production)
JWT_SECRET=your-super-secure-jwt-secret-here
APP_MEDIA_KEY=your-super-secure-media-key-here

# Database Connections
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/app_db
MONGO_URL=mongodb://root:example@localhost:27017

# OAuth (Optional - leave empty to disable)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Storage (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
APP_BUCKET=your-media-bucket
```

## 📊 Project Structure

```
FastApp/
├── app.py                          # Main application entry point
├── settings.py                     # Pydantic settings with validation
├── core/                           # Core framework
│   ├── config/                     # Configuration & validation
│   ├── db/                         # Database adapters & repositories
│   ├── middleware/                 # Security, auth context, error handling
│   ├── routes/                     # Core HTTP routes
│   ├── services/                   # Business logic
│   ├── ui/                         # UI components & layouts
│   ├── state/                      # State management
│   ├── workflows/                  # Workflow orchestration
│   └── utils/                      # Utilities
├── add_ons/                        # Domain modules
│   └── domains/                    # Domain add-ons
│       ├── blog/                   # Blog domain (posts, categories, comments)
│       ├── commerce/               # E-commerce domain
│       ├── lms/                    # Learning Management System
│       ├── social/                 # Social networking domain
│       └── stream/                 # Streaming domain
├── examples/                       # Working example apps
│   ├── social/                     # Enhanced social network
│   ├── streaming/                  # Streaming platform
│   ├── lms/                        # LMS example
│   └── ui/                         # Shared UI components
├── docs/                           # Technical documentation
├── public/                         # Static assets
└── pyproject.toml                  # Dependencies
```

## 🎯 Getting Started

### 1. Install Dependencies

```bash
uv pip install -e .
# or
pip install -e .
```

### 2. Start the Application

```bash
# Demo mode (recommended for testing)
DEMO_MODE=true uv run python app.py

# Production mode
uv run python app.py
```

### 3. Explore the Examples

- **Home**: `http://localhost:5001/`
- **Social Network**: `http://localhost:5001/social-example`
- **Streaming Platform**: `http://localhost:5001/streaming-example`
- **LMS**: `http://localhost:5001/lms-example`
- **E-Shop**: `http://localhost:5001/eshop-example`
- **Blog**: `http://localhost:5001/blog`

### 4. Test Authentication

1. Click "Register" in the navigation
2. Choose a role (Student, Instructor, Shop Owner, etc.)
3. Complete registration
4. Login and explore role-based redirects
5. Try the free product/course in E-Shop or LMS

### 5. Admin Dashboard

1. Login with admin credentials: `admin@freelancer.dev` / `AdminPass123!`
2. Access admin dashboard: `http://localhost:5001/admin/dashboard`
3. Explore site editing and theme customization

## 🚀 Use Cases

### For Freelance Developers

- **Quick prototypes** - Show clients working demos in minutes
- **Template library** - Start projects with proven patterns
- **Modular architecture** - Mix and match features
- **Client presentations** - Professional examples ready to go
- **Production deployment** - Scalable architecture included

### For Clients

- **E-commerce sites** - Online stores with cart and checkout
- **Learning platforms** - Course management and enrollment
- **Social networks** - Community platforms with profiles and messaging
- **Streaming services** - Video platforms with live and VOD
- **Blog systems** - Content management with SEO

### For Enterprises

- **Internal tools** - Admin dashboards and management systems
- **Multi-tenant platforms** - Scalable multi-site architecture
- **API backends** - RESTful APIs with authentication
- **Microservices foundation** - Modular domain system

## 🏗️ Architecture Highlights

### Domain-Driven Design

- **Modular domains** - Each domain is self-contained
- **Clean architecture** - Clear separation of concerns
- **Scalable design** - Easy to add new domains
- **Production ready** - Comprehensive error handling and logging

### Security First

- **Multi-role authentication** - Hierarchical permission system
- **Input sanitization** - XSS and SQL injection protection
- **Rate limiting** - Request throttling per IP
- **CSRF protection** - Token-based CSRF protection
- **Security headers** - CSP, X-Frame-Options, HSTS

### Performance Optimized

- **Connection pooling** - Efficient database connections
- **Caching layer** - Redis for session and data caching
- **Async operations** - Non-blocking I/O throughout
- **Responsive design** - Mobile-first performance

## 🤝 Contributing

The platform is modular and extensible. Each domain add-on is self-contained in `add_ons/domains/`.

To create a new domain:

1. Create a new directory in `add_ons/domains/`
2. Add models, services, routes, and UI components
3. Create a manifest file for domain metadata
4. Mount it in the add-on loader
5. Add example app in `examples/`

### 📋 Continuous Improvement TODOs

- [ ] **Enhanced Social Features**

  - [ ] Add story/ephemeral posts (24-hour expiration)
  - [ ] Implement groups and communities
  - [ ] Add reactions beyond likes (emoji reactions)
  - [ ] Social media analytics dashboard
- [ ] **Advanced Streaming**

  - [ ] Screen sharing capabilities
  - [ ] Multi-language subtitle support
  - [ ] Stream recording and VOD management
  - [ ] Pay-per-view streaming with access control
- [ ] **E-Commerce Enhancements**

  - [ ] Product reviews and ratings system
  - [ ] Inventory management dashboard
  - [ ] Advanced shipping options
  - [ ] Customer analytics and reporting
- [ ] **LMS Improvements**

  - [ ] Video lesson hosting and streaming
  - [ ] Quiz and assessment system
  - [ ] Certificate generation with templates
  - [ ] Course completion analytics
- [ ] **Platform Infrastructure**

  - [ ] Real-time notifications system
  - [ ] Advanced search with Elasticsearch
  - [ ] Multi-language support (i18n)
  - [ ] Mobile app API endpoints
- [ ] **Developer Experience**

  - [ ] CLI tool for rapid domain creation
  - [ ] Automated testing suite expansion
  - [ ] Performance monitoring dashboard
  - [ ] API documentation with OpenAPI/Swagger
- [ ] **Security & Performance**

  - [ ] Advanced rate limiting with Redis
  - [ ] Content Security Policy (CSP) optimization
  - [ ] Database query optimization
  - [ ] Caching layer improvements

### Development Workflow

```bash
# Start development environment
docker compose up -d

# Run tests
uv run pytest -q

# Integration tests
RUN_INTEGRATION_TESTS=1 uv run pytest -q tests/integration
```

## 📄 License

Apache 2.0

---

## 🎉 Current Status

**✅ Production Ready!**

- ✅ **Enhanced Authentication** - Multi-role system with permission enforcement
- ✅ **Social Network** - Complete social platform with posts, comments, likes, follows, DMs
- ✅ **Streaming Platform** - WebRTC-based streaming with video and chat
- ✅ **LMS System** - Course management with enrollment and progress tracking
- ✅ **E-Shop** - Full e-commerce with cart and checkout
- ✅ **Blog System** - Content management with admin interface
- ✅ **Documentation** - Comprehensive guides and architecture docs
- ✅ **Production Architecture** - Scalable modular monolith with polyglot persistence

**Ready for production deployment with comprehensive documentation and proven architecture!** 🚀
