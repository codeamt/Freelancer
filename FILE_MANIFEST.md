# File Manifest

Complete listing of important files in the codebase, organized by category.

---

## Documentation

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Architecture overview and design patterns |
| `CODEBASE_INDEX.md` | Quick navigation guide for LLMs |
| `FILE_MANIFEST.md` | This file - complete file listing |
| `README.md` | Project overview and setup |
| `docs/TYPE_SAFETY.md` | Type safety with Pydantic guide |
| `docs/PYDANTIC_USAGE.md` | Pydantic usage examples |
| `docs/ERROR_HANDLING.md` | Error handling guide |
| `docs/DEPENDENCY_INJECTION_GUIDE.md` | DI migration guide |
| `docs/GLOBAL_SINGLETONS_AUDIT.md` | Global singleton audit |

---

## Configuration

| File | Purpose |
|------|---------|
| `.env` | Environment variables (not in repo) |
| `env.example.txt` | Example environment variables with generation commands |
| `docker-compose.yml` | Local development services |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Project configuration |

---

## Core Framework

### Configuration & Validation
| File | Purpose |
|------|---------|
| `app/core/config/validation.py` | Startup configuration validation |
| `app/core/config/settings_facade.py` | Role-aware settings access |
| `app/settings.py` | Global settings |

### Exceptions & Error Handling
| File | Purpose |
|------|---------|
| `app/core/exceptions.py` | Custom exception hierarchy (15+ exceptions) |
| `app/core/middleware/error_handler.py` | Centralized error handler middleware |

### Dependency Injection
| File | Purpose |
|------|---------|
| `app/core/di/dependencies.py` | DI helper functions (15+ dependencies) |
| `app/core/di/container.py` | ExecutionContext, ServiceContainer, IntegrationContainer |
| `app/core/di/__init__.py` | DI exports |

### Database Layer
| File | Purpose |
|------|---------|
| `app/core/db/adapters/postgres.py` | PostgreSQL adapter |
| `app/core/db/adapters/mongodb.py` | MongoDB adapter |
| `app/core/db/adapters/redis.py` | Redis adapter |
| `app/core/db/adapters/duckdb.py` | DuckDB adapter |
| `app/core/db/repositories/user_repository.py` | User repository |
| `app/core/db/repositories/product_repository.py` | Product repository |
| `app/core/db/session.py` | Session management |
| `app/core/db/transaction_manager.py` | 2PC transaction coordinator |
| `app/core/db/connection_pool.py` | Connection pooling |
| `app/core/db/base_class.py` | Base database classes |

### Authentication & Authorization
| File | Purpose |
|------|---------|
| `app/core/services/auth/auth_service.py` | Auth business logic (login, refresh, verify) |
| `app/core/services/auth/models.py` | Pydantic models (User, LoginRequest/Response, TokenPayload) |
| `app/core/services/auth/user_service.py` | User management |
| `app/core/services/auth/context.py` | UserContext, PermissionContext |
| `app/core/services/auth/decorators.py` | @require_auth, @requires_permission |
| `app/core/services/auth/permissions.py` | Permission definitions and registry |
| `app/core/services/auth/helpers.py` | Auth helper functions |
| `app/core/services/auth/utils.py` | Auth utilities |
| `app/core/services/auth/security.py` | Security utilities |
| `app/core/services/auth/providers/jwt.py` | JWT provider |
| `app/core/services/auth/providers/oauth.py` | OAuth provider |
| `app/core/services/auth/providers/adapters/google_oauth.py` | Google OAuth adapter |
| `app/core/services/auth/__init__.py` | Auth exports |

### Services
| File | Purpose |
|------|---------|
| `app/core/services/db_service.py` | Database service |
| `app/core/services/settings/service.py` | Settings service |
| `app/core/services/settings/registry.py` | Settings registry |
| `app/core/services/settings/encryption.py` | Encryption service |
| `app/core/services/settings/session.py` | Settings session manager |
| `app/core/services/admin/admin_service.py` | Admin service |
| `app/core/services/cart/cart_service.py` | Cart service |
| `app/core/services/cart/redis_cart_service.py` | Redis cart service |
| `app/core/services/product/product_service.py` | Product service |
| `app/core/services/order/order_service.py` | Order service |
| `app/core/services/payment/payment_service.py` | Payment service |

### Integrations
| File | Purpose |
|------|---------|
| `app/core/integrations/storage/s3_client.py` | S3/MinIO storage client |
| `app/core/integrations/storage/models.py` | Storage Pydantic models (FileUpload, UploadUrl, etc.) |
| `app/core/integrations/storage/__init__.py` | Storage exports |
| `app/core/integrations/huggingface/huggingface_client.py` | HuggingFace AI client |
| `app/core/integrations/huggingface/models.py` | AI Pydantic models (TextGeneration, Classification, etc.) |
| `app/core/integrations/huggingface/__init__.py` | HuggingFace exports |
| `app/core/integrations/email/` | Email providers |
| `app/core/integrations/payment/` | Payment gateways |
| `app/core/integrations/analytics/consent_manager.py` | Cookie consent manager |

### State Management
| File | Purpose |
|------|---------|
| `app/core/state/state.py` | Immutable State container |
| `app/core/state/actions.py` | Action base class |
| `app/core/state/builder.py` | StateMachineApplication builder |
| `app/core/state/persistence.py` | MongoDB state persistence |
| `app/core/state/transitions.py` | Transition conditions |
| `app/core/state/__init__.py` | State exports |

### Workflows
| File | Purpose |
|------|---------|
| `app/core/workflows/admin.py` | SiteWorkflowManager, site creation workflows |
| `app/core/workflows/preview.py` | PreviewPublishManager, preview/publish actions |
| `app/core/workflows/__init__.py` | Workflow exports |

### Middleware
| File | Purpose |
|------|---------|
| `app/core/middleware/error_handler.py` | Error handling middleware |
| `app/core/middleware/security.py` | Security headers, CSRF, rate limiting |
| `app/core/middleware/auth_context.py` | User context injection |
| `app/core/middleware/redis_session.py` | Redis session management |
| `app/core/middleware/__init__.py` | Middleware exports |

### UI Components
| File | Purpose |
|------|---------|
| `app/core/ui/layout.py` | Layout components |
| `app/core/ui/components/auth.py` | LoginForm, RegisterForm |
| `app/core/ui/components/base.py` | Base components |
| `app/core/ui/components/consent_banner.py` | Cookie consent banner |
| `app/core/ui/components/content.py` | Content components |
| `app/core/ui/components/forms.py` | Form components |
| `app/core/ui/components/marketing.py` | Marketing components |
| `app/core/ui/components/__init__.py` | Component exports |
| `app/core/ui/state/config.py` | Component configuration |
| `app/core/ui/state/actions.py` | UI actions (AddComponent, RemoveComponent) |
| `app/core/ui/state/factory.py` | Component rendering |
| `app/core/ui/theme/editor.py` | Theme system |
| `app/core/ui/pages/` | Page templates |

### Utilities
| File | Purpose |
|------|---------|
| `app/core/utils/logger.py` | Centralized logging |
| `app/core/utils/security.py` | Security utilities |
| `app/core/utils/helpers.py` | General helpers |
| `app/core/utils/cache.py` | Caching utilities |
| `app/core/utils/cookies.py` | Cookie utilities |
| `app/core/utils/files.py` | File utilities |
| `app/core/utils/responses.py` | Unified response helpers |
| `app/core/utils/app_factory.py` | App creation helpers |

### Routes
| File | Purpose |
|------|---------|
| `app/routes/auth.py` | Authentication routes |
| `app/routes/main.py` | Main routes |
| `app/routes/admin_sites.py` | Admin site management routes |
| `app/routes/admin_users.py` | Admin user management routes |
| `app/routes/settings.py` | Settings routes |
| `app/routes/editor.py` | Visual editor routes |
| `app/routes/oauth.py` | OAuth routes |
| `app/routes/profile.py` | User profile routes |
| `app/routes/cart.py` | Cart routes |
| `app/routes/__init__.py` | Route exports |

### Add-on System
| File | Purpose |
|------|---------|
| `app/core/addon_loader.py` | Add-on loading and registration |
| `app/add_ons/services/event_bus_base.py` | Event bus |
| `app/add_ons/services/graphql.py` | GraphQL service |

---

## Domain Add-ons

### Commerce Domain
| File | Purpose |
|------|---------|
| `app/add_ons/domains/commerce/manifest.py` | Commerce domain manifest |
| `app/add_ons/domains/commerce/models/` | Commerce domain models |
| `app/add_ons/domains/commerce/repositories/` | Commerce repositories |
| `app/add_ons/domains/commerce/services/` | Commerce services |
| `app/add_ons/domains/commerce/routes/` | Commerce routes |

### LMS Domain
| File | Purpose |
|------|---------|
| `app/add_ons/domains/lms/manifest.py` | LMS domain manifest |
| `app/add_ons/domains/lms/models/` | LMS domain models |
| `app/add_ons/domains/lms/repositories/` | LMS repositories |
| `app/add_ons/domains/lms/services/` | LMS services |
| `app/add_ons/domains/lms/routes/` | LMS routes |

### Social Domain
| File | Purpose |
|------|---------|
| `app/add_ons/domains/social/manifest.py` | Social domain manifest |
| `app/add_ons/domains/social/models/` | Social domain models |
| `app/add_ons/domains/social/repositories/` | Social repositories |
| `app/add_ons/domains/social/services/` | Social services |
| `app/add_ons/domains/social/routes/` | Social routes |

### Stream Domain
| File | Purpose |
|------|---------|
| `app/add_ons/domains/stream/manifest.py` | Stream domain manifest |
| `app/add_ons/domains/stream/models/` | Stream domain models |
| `app/add_ons/domains/stream/repositories/` | Stream repositories |
| `app/add_ons/domains/stream/services/` | Stream services |
| `app/add_ons/domains/stream/routes/` | Stream routes |

---

## Application Entry Points

| File | Purpose |
|------|---------|
| `app/app.py` | Main application initialization |
| `app/main.py` | Application entry point |

---

## Key Patterns by File

### Pydantic Models (Type Safety)
- `app/core/services/auth/models.py` - Auth models
- `app/core/integrations/storage/models.py` - Storage models
- `app/core/integrations/huggingface/models.py` - AI models

### Exception Handling
- `app/core/exceptions.py` - Exception definitions
- `app/core/middleware/error_handler.py` - Exception middleware

### Dependency Injection
- `app/core/di/dependencies.py` - DI functions
- `app/app.py` - Service initialization

### Database Operations
- `app/core/db/repositories/*.py` - Repository pattern
- `app/core/db/transaction_manager.py` - Transactions

### State Management
- `app/core/state/*.py` - State pattern
- `app/core/workflows/*.py` - Workflow orchestration

---

## Testing Files

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Shared test fixtures |
| `tests/unit/` | Unit tests |
| `tests/integration/` | Integration tests |
| `tests/fixtures/` | Test data |

---

## File Count Summary

- **Documentation**: 9 files
- **Configuration**: 5 files
- **Core Framework**: 100+ files
- **Domain Add-ons**: 20+ files per domain
- **Tests**: 50+ files

**Total Important Files**: ~200+

---

## Quick Search Guide

### Find by Feature

**Authentication**: `app/core/services/auth/`
**Database**: `app/core/db/`
**Error Handling**: `app/core/exceptions.py`, `app/core/middleware/error_handler.py`
**Type Safety**: `*/models.py` files
**Dependency Injection**: `app/core/di/`
**State Management**: `app/core/state/`
**UI Components**: `app/core/ui/`
**Integrations**: `app/core/integrations/`
**Routes**: `app/routes/`
**Add-ons**: `app/add_ons/domains/`

### Find by Pattern

**Pydantic Models**: Search for `models.py` files
**Repositories**: Search in `app/core/db/repositories/`
**Services**: Search in `app/core/services/`
**Middleware**: Search in `app/core/middleware/`
**Actions**: Search in `app/core/state/actions.py` or `*/actions.py`
**Routes**: Search in `app/routes/`

---

**Last Updated**: December 12, 2025
**Total Files Documented**: 200+
