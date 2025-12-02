# FastApp - Modular Web Application Platform

A modern, modular FastHTML platform with authentication, role-based access control, and ready-to-use example applications. Perfect for freelance developers building custom solutions for clients.

## 🚀 Quick Start

```bash
# Install dependencies
uv pip install -e .

# Start the application
cd app
python app.py
```

Visit: `http://localhost:5001`

**No database required!** The app runs in demo mode with in-memory storage by default.

## ✨ Features

### 🔐 Authentication System
- **JWT-based authentication** with bcrypt password hashing
- **Role-based access control** (user, student, instructor, admin)
- **User registration** with role selection
- **Smart redirects** - returns users to their original page after login
- **Demo mode** - works without database connection

### 🎯 Example Applications

Four fully-functional example apps to showcase different use cases:

#### 1. 🛍️ E-Shop (`/eshop-example`)
- Product catalog with search and filtering
- Shopping cart system
- Checkout flow
- **FREE product** for testing
- Product detail pages with features
- Auth-protected cart and checkout

#### 2. 📚 LMS (`/lms-example`)
- Course catalog with ratings and stats
- Student enrollment system
- "My Courses" dashboard
- **FREE orientation course**
- Course detail pages with syllabus
- Progress tracking

#### 3. 🌐 Social Network (`/social-example`)
- Coming soon page with feature preview
- Professional network templates
- Community platform examples
- Tech stack overview

#### 4. 📺 Streaming Platform (`/streaming-example`)
- Coming soon page with feature preview
- Live streaming templates
- VOD platform examples
- Multiple use case scenarios

### 🎨 UI Components
- **MonsterUI** - Beautiful, accessible components
- **DaisyUI** - Tailwind CSS component library
- **UIcons** - Icon system
- **Responsive design** - Mobile-first approach
- **Dark mode ready** - Theme support built-in

## 🛠️ Tech Stack

### Core
- **FastHTML** - Modern Python web framework with HTMX
- **MonsterUI** - Component library built on DaisyUI
- **Tailwind CSS** - Utility-first CSS framework
- **Python 3.11+** - Modern Python features

### Authentication & Security
- **JWT** - Token-based authentication
- **bcrypt** - Password hashing
- **Role-based access control** - Flexible permission system

### Optional (for production)
- **MongoDB** - User data and content storage
- **PostgreSQL** - Relational data (if needed)
- **Redis** - Session management and caching

## 📚 Documentation

### Core Documentation
- [Role System](ROLE_SYSTEM.md) - Role-based access control explained
- [E-Shop Auth Flow](ESHOP_AUTH_FLOW.md) - Authentication flow details
- [LMS Example README](app/examples/lms/README.md) - LMS features and usage
- [E-Shop Example README](app/examples/eshop/README.md) - E-Shop features and usage

### Architecture
- [App Integration Guide](APP_INTEGRATION_GUIDE.md) - Add-on system
- [Mount Examples](MOUNT_EXAMPLES.md) - How to mount example apps
- [Startup Checklist](STARTUP_CHECKLIST.md) - Troubleshooting guide

## 🔧 Configuration

### Demo Mode (Default)
No configuration needed! Just run `python app.py` and everything works with in-memory storage.

### Production Mode (Optional)
Create a `.env` file:
```bash
# MongoDB (optional)
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=fastapp

# JWT Secret
JWT_SECRET=your-secret-key-here

# Other services (optional)
REDIS_URL=redis://localhost:6379/0
```

## 📊 Project Structure

```
FastApp/
├── app/
│   ├── app.py                 # Main application entry point
│   ├── core/                  # Core application
│   │   ├── routes/            # Main routes
│   │   ├── services/          # Core services (DB, etc.)
│   │   ├── ui/                # UI components and layouts
│   │   │   ├── layout.py      # Main layout with navigation
│   │   │   ├── components.py  # Reusable UI components
│   │   │   └── pages/         # Core pages (home, etc.)
│   │   └── utils/             # Utilities (security, logger)
│   ├── add_ons/               # Add-on modules
│   │   └── auth/              # ✅ Authentication system
│   │       ├── routes/        # Auth routes (login, register)
│   │       ├── services/      # Auth service (JWT, bcrypt)
│   │       └── ui/            # Auth UI pages
│   └── examples/              # Example applications
│       ├── eshop/             # ✅ E-commerce example
│       ├── lms/               # ✅ Learning platform example
│       ├── social/            # 🚧 Social network (coming soon)
│       └── streaming/         # 🚧 Streaming platform (coming soon)
├── pyproject.toml             # Dependencies
└── README.md                  # This file
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
cd app
python app.py
```

### 3. Explore the Examples
- **Home**: `http://localhost:5001/`
- **E-Shop**: `http://localhost:5001/eshop-example`
- **LMS**: `http://localhost:5001/lms-example`
- **Social**: `http://localhost:5001/social-example`
- **Streaming**: `http://localhost:5001/streaming-example`

### 4. Test Authentication
1. Click "Register" in the navigation
2. Choose a role (Customer, Student, or Instructor)
3. Complete registration
4. Login and explore role-based redirects
5. Try the free product/course in E-Shop or LMS

## 🚀 Use Cases

### For Freelance Developers
- **Quick prototypes** - Show clients working demos in minutes
- **Template library** - Start projects with proven patterns
- **Modular architecture** - Mix and match features
- **Client presentations** - Professional examples ready to go

### For Clients
- **E-commerce sites** - Online stores with cart and checkout
- **Learning platforms** - Course management and enrollment
- **Social networks** - Community platforms with profiles
- **Streaming services** - Video platforms with live and VOD

## 🤝 Contributing

The platform is modular and extensible. Each example app is self-contained in `app/examples/`.

To create a new example:
1. Create a new directory in `app/examples/`
2. Add `__init__.py` and `app.py`
3. Mount it in `app/app.py`
4. Add to navigation in `app/core/ui/layout.py`

## 📄 License

Apache 2.0

---

**Status**: Auth system complete! Four example apps ready! �

