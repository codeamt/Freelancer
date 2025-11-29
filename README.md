# Freelancer Platform

A comprehensive platform with multiple add-ons for building modern web applications.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
cd app/core/migrations
alembic upgrade head

# Start the application
python -m app.core.app
```

Visit: `http://localhost:8002`

## 🎨 Landing Page System (NEW! - Phase 1 Complete)

Core now includes **10 production-ready landing page components** for creating marketing pages like Doodle Institute!

### Components Available
- ✅ Hero sections (with image/video backgrounds)
- ✅ Pricing cards with promotional badges
- ✅ Testimonial carousels
- ✅ FAQ accordions
- ✅ Countdown timers
- ✅ Feature grids
- ✅ Email capture forms
- ✅ CTA banners

**Example**: Visit `/doodle-example` to see all components in action!

See **[PHASE_1_COMPLETE.md](docs/PHASE_1_COMPLETE.md)** for full documentation.

---

## 🎓 LMS Add-on

The Learning Management System add-on is now **fully implemented and production-ready**!

### Features
- ✅ Course creation and management
- ✅ Student enrollment system
- ✅ Real-time progress tracking
- ✅ Assessments and grading
- ✅ Certificate generation
- ✅ Instructor dashboard
- ✅ Student dashboard

### Documentation
- **[LMS_INDEX.md](add_ons/lms/docs/LMS_INDEX.md)** - Documentation index
- **[LMS_COMPLETE.md](add_ons/lms/docs/LMS_COMPLETE.md)** - Overview
- **[LMS_QUICKSTART.md](add_ons/lms/docs/LMS_QUICKSTART.md)** - 5-minute setup
- **[LMS_API_REFERENCE.md](add_ons/lms/docs/LMS_API_REFERENCE.md)** - API docs
- **[LMS_DEPLOYMENT_CHECKLIST.md](add_ons/lms/docs/LMS_DEPLOYMENT_CHECKLIST.md)** - Deployment guide

### Quick LMS Setup
```bash
# Run LMS migration
cd app/core/migrations
alembic upgrade head

# Test LMS setup
python test_lms_setup.py

# Create sample courses (optional)
python seed_lms_data.py

# Start app
python -m app.core.app
```

Visit LMS: `http://localhost:8002/lms/courses`

## 📦 Add-ons

### Available
- **LMS** 🎓 - Learning Management System (100% complete)
- **Stream** 🎥 - Video streaming (structure in place)
- **Commerce** 💰 - E-commerce (planned)
- **Social** 👥 - Social networking (planned)

See **[ADD_ONS_TODO.md](ADD_ONS_TODO.md)** for the complete roadmap.

## 🛠️ Tech Stack

- **FastHTML** - Modern Python web framework
- **SQLAlchemy** - Async ORM
- **PostgreSQL** - Primary database
- **MongoDB** - Analytics and dynamic data
- **Redis** - Session management
- **Pydantic** - Data validation
- **Alembic** - Database migrations

## 📚 Documentation

- [LMS Documentation Index](add_ons/lms/docs/LMS_INDEX.md)
- [Add-ons Roadmap](add_ons/lms/docs/ADD_ONS_TODO.md)
- [Environment Setup](docs/ENV_TEMPLATE.md)
- [Google OAuth Setup](docs/GOOGLE_OAUTH_SETUP.md)

## 🔧 Configuration

Copy environment template:
```bash
# See ENV_TEMPLATE.md for all variables
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapp
REDIS_URL=redis://localhost:6379/0
```

## 🧪 Testing

```bash
# Test LMS setup
python app/tests/test_lms_setup.py

# Run all tests (when implemented)
pytest
```

## 📊 Project Structure

```
Freelancer/
├── app/
│   ├── core/              # Core application
│   │   ├── routes/        # Main routes
│   │   ├── services/      # Core services
│   │   ├── db/            # Database models
│   │   └── migrations/    # Alembic migrations
│   └── add_ons/           # Add-on modules
│       ├── lms/           # ✅ Learning Management System
│       ├── stream/        # Video streaming
│       ├── commerce/      # E-commerce
│       └── social/        # Social features
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## 🎯 Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure environment**: Copy `docs/ENV_TEMPLATE.md` to `.env`
3. **Run migrations**: `alembic upgrade head`
4. **Start application**: `python -m app.core.app`
5. **Visit LMS**: `http://localhost:8002/lms/courses`

## 📖 Learn More

- [LMS Complete Guide](app/add_ons/lms/docs/LMS_COMPLETE.md) - Everything about the LMS
- [Quick Start Guide](app/add_ons/lms/docs/LMS_QUICKSTART.md) - Get running in 5 minutes
- [API Reference](app/add_ons/lms/docs/LMS_API_REFERENCE.md) - Complete API documentation
- [Deployment Guide](app/add_ons/lms/docs/LMS_DEPLOYMENT_CHECKLIST.md) - Production deployment

## 🤝 Contributing

The platform is modular and extensible. Each add-on is self-contained in `app/add_ons/`.

## 📄 License

Apache 2.0

---

**Status**: LMS add-on is production-ready! 🎓

