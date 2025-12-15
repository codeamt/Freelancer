import os
import uuid

import pytest
import httpx

from collections import defaultdict


@pytest.fixture(scope="session")
def integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS") == "1"


@pytest.fixture(scope="session")
def postgres_url() -> str:
    return os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/app_db",
    )


@pytest.fixture(scope="session")
def unique_email_prefix() -> str:
    return f"it-{uuid.uuid4().hex[:10]}"


@pytest.fixture()
def unique_email(unique_email_prefix: str) -> str:
    return f"{unique_email_prefix}-{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture()
async def test_app(integration_enabled: bool, postgres_url: str):
    if not integration_enabled:
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    # Ensure required env vars exist for import-time checks
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-please-change-000000000000000000000000")
    os.environ.setdefault("APP_MEDIA_KEY", "test-media-key-please-change-000000000000000000000000")

    from fasthtml.common import FastHTML
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    from core.db.adapters.postgres_adapter import PostgresAdapter
    from core.db.repositories.user_repository import UserRepository
    from core.services.auth.providers.jwt import JWTProvider
    from core.services.auth import AuthService, UserService

    from core.middleware.security import RateLimitMiddleware, SecurityMiddleware, _BUCKET
    from core.routes.auth import router_auth

    from examples.eshop import create_eshop_app
    from examples.lms import create_lms_app

    class _InMemoryMongo:
        def __init__(self):
            self._cols = defaultdict(list)

        def _match(self, doc: dict, flt: dict) -> bool:
            for k, v in (flt or {}).items():
                if doc.get(k) != v:
                    return False
            return True

        async def insert_one(self, collection: str, document: dict, transaction_id=None) -> str:
            doc = dict(document)
            self._cols[collection].append(doc)
            return "inmem"

        async def find_one(self, collection: str, filter: dict, projection=None):
            for doc in self._cols[collection]:
                if self._match(doc, filter):
                    return dict(doc)
            return None

        async def find_many(self, collection: str, filter: dict, projection=None, limit: int = 100, skip: int = 0, sort=None):
            results = [dict(d) for d in self._cols[collection] if self._match(d, filter)]
            return results[skip: skip + limit]

        async def update_one(self, collection: str, filter: dict, update: dict, transaction_id=None) -> int:
            for doc in self._cols[collection]:
                if self._match(doc, filter):
                    doc.update(update)
                    return 1
            return 0

        async def delete_one(self, collection: str, filter: dict, transaction_id=None) -> int:
            for i, doc in enumerate(self._cols[collection]):
                if self._match(doc, filter):
                    del self._cols[collection][i]
                    return 1
            return 0

    # Reset rate limiter state between tests
    _BUCKET.clear()

    # Connect Postgres + ensure schema
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=1, max_size=2)
    try:
        await postgres.connect()
    except Exception as e:
        pytest.skip(f"Postgres not reachable at {postgres_url}: {e}")

    from core.db.init_schema import CORE_SCHEMA_SQL
    await postgres.execute(CORE_SCHEMA_SQL)

    user_repo = UserRepository(postgres=postgres)
    jwt_provider = JWTProvider()
    auth_service = AuthService(user_repository=user_repo, jwt_provider=jwt_provider)
    user_service = UserService(user_repository=user_repo)

    app = FastHTML()
    # Provide required services on app.state (mirrors app/app.py patterns)
    app.state.postgres = postgres
    app.state.user_repository = user_repo
    app.state.jwt_provider = jwt_provider
    app.state.auth_service = auth_service
    app.state.user_service = user_service

    # Mount example apps used by integration tests.
    inmem_mongo = _InMemoryMongo()
    eshop_app = create_eshop_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=None,
        redis=None,
        demo=True,
    )
    lms_app = create_lms_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=inmem_mongo,
        redis=None,
        demo=True,
    )
    app.mount("/eshop-example", eshop_app)
    app.mount("/lms-example", lms_app)

    # Middleware needed so routes can read request.state.sanitized_form
    # and for SEC integration tests.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityMiddleware)

    # Test-only helper routes for inspecting sanitization results.
    @app.get("/_test/ping")
    async def _ping(request: Request):
        return JSONResponse({"ok": True})

    @app.post("/_test/echo")
    async def _echo(request: Request):
        return JSONResponse(
            {
                "form": getattr(request.state, "sanitized_form", None),
                "query": getattr(request.state, "sanitized_query", None),
                "headers": getattr(request.state, "sanitized_headers", None),
            }
        )

    # Mount auth routes
    router_auth.to_app(app)

    try:
        yield app
    finally:
        await postgres.disconnect()


@pytest.fixture()
async def async_client(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=False) as ac:
        yield ac


@pytest.fixture()
async def test_app_production(integration_enabled: bool, postgres_url: str):
    if not integration_enabled:
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    prev_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"

    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-please-change-000000000000000000000000")
    os.environ.setdefault("APP_MEDIA_KEY", "test-media-key-please-change-000000000000000000000000")

    try:
        from fasthtml.common import FastHTML
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        from core.db.adapters.postgres_adapter import PostgresAdapter
        from core.db.repositories.user_repository import UserRepository
        from core.services.auth.providers.jwt import JWTProvider
        from core.services.auth import AuthService, UserService

        from core.middleware.security import RateLimitMiddleware, SecurityMiddleware, _BUCKET
        from core.routes.auth import router_auth

        # Reset rate limiter state between tests
        _BUCKET.clear()

        postgres = PostgresAdapter(connection_string=postgres_url, min_size=1, max_size=2)
        try:
            await postgres.connect()
        except Exception as e:
            pytest.skip(f"Postgres not reachable at {postgres_url}: {e}")

        from core.db.init_schema import CORE_SCHEMA_SQL
        await postgres.execute(CORE_SCHEMA_SQL)

        user_repo = UserRepository(postgres=postgres)
        jwt_provider = JWTProvider()
        auth_service = AuthService(user_repository=user_repo, jwt_provider=jwt_provider)
        user_service = UserService(user_repository=user_repo)

        app = FastHTML()
        app.state.postgres = postgres
        app.state.user_repository = user_repo
        app.state.jwt_provider = jwt_provider
        app.state.auth_service = auth_service
        app.state.user_service = user_service

        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(SecurityMiddleware)

        @app.get("/_test/ping")
        async def _ping(request: Request):
            return JSONResponse({"ok": True})

        @app.post("/_test/echo")
        async def _echo(request: Request):
            return JSONResponse(
                {
                    "form": getattr(request.state, "sanitized_form", None),
                    "query": getattr(request.state, "sanitized_query", None),
                    "headers": getattr(request.state, "sanitized_headers", None),
                }
            )

        router_auth.to_app(app)

        try:
            yield app
        finally:
            await postgres.disconnect()
    finally:
        if prev_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = prev_env


@pytest.fixture()
async def async_client_production(test_app_production):
    transport = httpx.ASGITransport(app=test_app_production)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=False) as ac:
        yield ac
