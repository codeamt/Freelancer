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
| `TODOS.md` | Comprehensive production-ready TODOs organized by component |
| `DEVELOPMENT_TODOS.md` | Legacy development roadmap (archived) |
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
| `core/config/validation.py` | Startup configuration validation |
| `core/config/settings_facade.py` | Role-aware settings access |
| `settings.py` | Global settings |

### Exceptions & Error Handling
| File | Purpose |
|------|---------|
| `core/exceptions.py` | Custom exception hierarchy (15+ exceptions) |
| `core/middleware/error_handler.py` | Centralized error handler middleware |

### Dependency Injection
| File | Purpose |
|------|---------|
| `core/di/dependencies.py` | DI helper functions (15+ dependencies) |
| `core/di/container.py` | ExecutionContext, ServiceContainer, IntegrationContainer |
| `core/di/__init__.py` | DI exports |

### Database Layer
| File | Purpose |
|------|---------|
| `core/db/adapters/postgres_adapter.py` | PostgreSQL adapter |
| `core/db/adapters/mongodb_adapter.py` | MongoDB adapter |
| `core/db/adapters/redis_adapter.py` | Redis adapter |
| `core/db/adapters/duckdb_adapter.py` | DuckDB adapter |
| `core/db/adapters/minio_adapter.py` | MinIO (S3-compatible) adapter |
| `core/db/repositories/user_repository.py` | User repository |
| `core/db/session.py` | Session management |
| `core/db/transaction_manager.py` | 2PC transaction coordinator |
| `core/db/connection_pool.py` | Connection pooling |
| `core/db/base_class.py` | Base database classes |

### Authentication & Authorization
| File | Purpose |
|------|---------|
| `core/services/auth/auth_service.py` | Auth business logic (login, refresh, verify) |
| `core/services/auth/enforcement.py` | Role-based enforcement decorators and permission checking |
| `core/services/auth/models.py` | Pydantic models (User, LoginRequest/Response, TokenPayload, UserRole enum) |
| `core/services/auth/user_service.py` | User management |
| `core/services/auth/context.py` | UserContext, PermissionContext |
| `core/services/auth/decorators.py` | @require_auth, @requires_permission |
| `core/services/auth/permissions.py` | Permission definitions and registry |
| `core/services/auth/helpers.py` | Auth helper functions |
| `core/services/auth/utils.py` | Auth utilities |
| `core/services/auth/security.py` | Security utilities |
| `core/services/auth/providers/jwt.py` | JWT provider |
| `core/services/auth/providers/oauth.py` | OAuth provider |
| `core/services/auth/providers/adapters/google_oauth.py` | Google OAuth adapter |
| `core/services/auth/__init__.py` | Auth exports |

### Services
| File | Purpose |
|------|---------|
| `core/services/db_service.py` | Database service |
| `core/services/settings/service.py` | Settings service |
| `core/services/settings/registry.py` | Settings registry |
| `core/services/settings/encryption.py` | Encryption service |
| `core/services/settings/session.py` | Settings session manager |
| `core/services/admin/admin_service.py` | Admin service |
| `core/services/cart/cart_service.py` | Cart service |
| `core/services/cart/redis_cart_service.py` | Redis cart service |
| `core/services/product/product_service.py` | Product service |
| `core/services/order/order_service.py` | Order service |
| `core/services/payment/payment_service.py` | Payment service |

### Integrations
| File | Purpose |
|------|---------|
| `core/integrations/storage/s3_client.py` | S3/MinIO storage client |
| `core/integrations/storage/models.py` | Storage Pydantic models (FileUpload, UploadUrl, etc.) |
| `core/integrations/storage/__init__.py` | Storage exports |
| `core/integrations/huggingface/huggingface_client.py` | HuggingFace AI client |
| `core/integrations/huggingface/models.py` | AI Pydantic models (TextGeneration, Classification, etc.) |
| `core/integrations/huggingface/__init__.py` | HuggingFace exports |
| `core/integrations/email/` | Email providers |
| `core/integrations/payment/` | Payment gateways |
| `core/integrations/analytics/consent_manager.py` | Cookie consent manager |

### State Management
| File | Purpose |
|------|---------|
| `core/state/state.py` | Immutable State container |
| `core/state/actions.py` | Action base class |
| `core/state/builder.py` | StateMachineApplication builder |
| `core/state/persistence.py` | MongoDB state persistence |
| `core/state/transitions.py` | Transition conditions |
| `core/state/__init__.py` | State exports |

### Workflows
| File | Purpose |
|------|---------|
| `core/workflows/admin.py` | SiteWorkflowManager, site creation workflows |
| `core/workflows/preview.py` | PreviewPublishManager, preview/publish actions |
| `core/workflows/__init__.py` | Workflow exports |

### Middleware
| File | Purpose |
|------|---------|
| `core/middleware/error_handler.py` | Error handling middleware |
| `core/middleware/security.py` | Security headers, CSRF, rate limiting |
| `core/middleware/auth_context.py` | User context injection |
| `core/middleware/redis_session.py` | Redis session management |
| `core/middleware/__init__.py` | Middleware exports |

### UI Components
| File | Purpose |
|------|---------|
| `core/ui/layout.py` | Layout components |
| `core/ui/components/auth.py` | LoginForm, RegisterForm |
| `core/ui/components/base.py` | Base components |
| `core/ui/components/consent_banner.py` | Cookie consent banner |
| `core/ui/components/content.py` | Content components |
| `core/ui/components/forms.py` | Form components |
| `core/ui/components/marketing.py` | Marketing components |
| `core/ui/components/__init__.py` | Component exports |
| `core/ui/state/config.py` | Component configuration |
| `core/ui/state/actions.py` | UI actions (AddComponent, RemoveComponent) |
| `core/ui/state/factory.py` | Component rendering |
| `core/ui/theme/editor.py` | Theme system |
| `core/ui/pages/` | Page templates |

### Utilities
| File | Purpose |
|------|---------|
| `core/utils/logger.py` | Centralized logging |
| `core/utils/security.py` | Security utilities |
| `core/utils/helpers.py` | General helpers |
| `core/utils/cache.py` | Caching utilities |
| `core/utils/cookies.py` | Cookie utilities |
| `core/utils/files.py` | File utilities |
| `core/utils/responses.py` | Unified response helpers |
| `core/utils/app_factory.py` | App creation helpers |

### Routes
| File | Purpose |
|------|---------|
| `core/routes/auth.py` | Authentication routes (including web admin login/dashboard) |
| `core/routes/main.py` | Main routes |
| `core/routes/admin_sites.py` | Admin site management routes (component editor, theme editor, preview/publish) |
| `core/routes/admin_users.py` | Admin user management routes |
| `core/routes/settings.py` | Settings routes |
| `core/routes/editor.py` | Visual editor routes |
| `core/routes/oauth.py` | OAuth routes |
| `core/routes/profile.py` | User profile routes |
| `core/routes/cart.py` | Cart routes |
| `core/routes/__init__.py` | Route exports |

### Add-on System
| File | Purpose |
|------|---------|
| `core/addon_loader.py` | Add-on loading and registration |
| `add_ons/services/event_bus_base.py` | Event bus |
| `add_ons/services/graphql.py` | GraphQL service |

---

## Domain Add-ons

### Blog Domain
| File | Purpose |
|------|---------|
| `add_ons/domains/blog/manifest.py` | Blog domain manifest |
| `add_ons/domains/blog/services/post_service.py` | Blog PostService (demo + optional DB mode) |
| `add_ons/domains/blog/routes/posts.py` | Blog routes (`/blog`, create/view) |
| `add_ons/domains/blog/ui/` | Blog pages/components |
| `add_ons/domains/blog/models/` | Blog domain models |
| `add_ons/domains/blog/repositories/` | Blog repositories |
| `add_ons/domains/blog/ui/components.py` | Blog UI components |

### Commerce Domain
| File | Purpose |
|------|---------|
| `add_ons/domains/commerce/manifest.py` | Commerce domain manifest |
| `add_ons/domains/commerce/models/` | Commerce domain models |
| `add_ons/domains/commerce/repositories/` | Commerce repositories |
| `add_ons/domains/commerce/services/` | Commerce services |
| `add_ons/domains/commerce/routes/` | Commerce routes |
| `add_ons/domains/commerce/ui/` | Commerce UI components |

### LMS Domain
| File | Purpose |
|------|---------|
| `add_ons/domains/lms/manifest.py` | LMS domain manifest |
| `add_ons/domains/lms/models/` | LMS domain models |
| `add_ons/domains/lms/repositories/` | LMS repositories |
| `add_ons/domains/lms/services/` | LMS services |
| `add_ons/domains/lms/routes/` | LMS routes |
| `add_ons/domains/lms/ui/` | LMS UI components |

### Social Domain
| File | Purpose |
|------|---------|
| `add_ons/domains/social/manifest.py` | Social domain manifest |
| `add_ons/domains/social/models/` | Social domain models (Post, Comment, Like, Follow, Conversation, DirectMessage) |
| `add_ons/domains/social/repositories/` | Social repositories |
| `add_ons/domains/social/services/` | Social services (SocialService, DirectMessageService) |
| `add_ons/domains/social/routes/` | Social routes |
| `add_ons/domains/social/ui/components.py` | Social UI components (PostComposer, PostCard, UserCard, etc.) |
| `add_ons/domains/social/ui/__init__.py` | Social UI exports |

### Stream Domain
| File | Purpose |
|------|---------|
| `add_ons/domains/stream/manifest.py` | Stream domain manifest |
| `add_ons/domains/stream/models/` | Stream domain models |
| `add_ons/domains/stream/services/` | Stream services |
| `add_ons/domains/stream/routes/` | Stream routes |
| `add_ons/domains/stream/ui/` | Stream UI components |

---

## Example Applications

### Social Example App
| File | Purpose |
|------|---------|
| `examples/social/app.py` | Social network example application with enhanced UI |
| `examples/social/ui/components.py` | Shared UI components for social and streaming apps |
| `examples/social/__init__.py` | Social example app exports |

### Streaming Example App
| File | Purpose |
|------|---------|
| `examples/streaming/app.py` | Streaming platform example application |
| `examples/streaming/ui/components.py` | Streaming UI components (VideoStreamCard, StreamingHomePage) |
| `examples/streaming/__init__.py` | Streaming example app exports |

### LMS Example App
| File | Purpose |
|------|---------|
| `examples/lms/app.py` | Learning Management System example application |
| `examples/lms/__init__.py` | LMS example app exports |

---

## Application Entry Points

| File | Purpose |
|------|---------|
| `app.py` | Main application initialization |
| `core/app_factory.py` | App factory used by example apps/tests and non-demo Blog mounting |
| `core/bootstrap.py` | Application bootstrap and service initialization |
| `core/mounting.py` | Route mounting and example app registration |

---

## Key Patterns by File

### Pydantic Models (Type Safety)
- `core/services/auth/models.py` - Auth models
- `core/integrations/storage/models.py` - Storage models
- `core/integrations/huggingface/models.py` - AI models
- `add_ons/domains/*/models/` - Domain-specific models

### Exception Handling
- `core/exceptions.py` - Exception definitions
- `core/middleware/error_handler.py` - Exception middleware

### Dependency Injection
- `core/di/dependencies.py` - DI functions
- `app.py` - Service initialization

### Database Operations
- `core/db/repositories/*.py` - Repository pattern
- `core/db/transaction_manager.py` - Transactions

### State Management
- `core/state/*.py` - State pattern
- `core/workflows/*.py` - Workflow orchestration

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

- **Documentation**: 12 files
- **Configuration**: 5 files
- **Core Framework**: 100+ files
- **Domain Add-ons**: 30+ files per domain (150+ total)
- **Example Applications**: 6 files
- **Tests**: 50+ files

**Total Important Files**: ~300+

---

## Quick Search Guide

### Find by Feature

**Authentication**: `core/services/auth/`
**Database**: `core/db/`
**Error Handling**: `core/exceptions.py`, `core/middleware/error_handler.py`
**Type Safety**: `*/models.py` files
**Dependency Injection**: `core/di/`
**State Management**: `core/state/`
**UI Components**: `core/ui/`
**Integrations**: `core/integrations/`
**Routes**: `core/routes/`
**Add-ons**: `add_ons/domains/`
**Examples**: `examples/`

### Find by Pattern

**Pydantic Models**: Search for `models.py` files
**Repositories**: Search in `core/db/repositories/`
**Services**: Search in `core/services/`
**Middleware**: Search in `core/middleware/`
**Actions**: Search in `core/state/actions.py` or `*/actions.py`
**Routes**: Search in `core/routes/`
**UI Components**: Search in `*/ui/components.py`

---

## Recent Major Updates

### December 2025 Updates
- ✅ Added comprehensive `TODOS.md` with production-ready roadmap
- ✅ Enhanced social example app with sleek UI and full domain features
- ✅ Updated social domain with complete models (Post, Comment, Like, Follow, Conversation, DirectMessage)
- ✅ Added streaming example app with UI components
- ✅ Improved example app structure with shared UI components
- ✅ Enhanced authentication and authorization system
- ✅ Added multi-role support and role hierarchy

### Architecture Improvements
- ✅ Modular domain system with independent add-ons
- ✅ Enhanced UI component library with MonsterUI
- ✅ Improved error handling and middleware system
- ✅ Better dependency injection and service management
- ✅ Enhanced state management and workflows

---

**Last Updated**: December 21, 2025
**Total Files Documented**: 300+
**Recent Changes**: Added TODOS.md, enhanced social/streaming examples, updated domain structure
