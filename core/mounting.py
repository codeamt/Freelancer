from core.utils.logger import get_logger

from core.routes import (
    router_main,
    router_editor,
    router_admin_sites,
    router_admin_users,
    router_admin_roles,
    router_auth,
    router_settings,
    router_profile,
    router_oauth,
    router_cart,
)

from core.addon_loader import get_addon_loader, get_enabled_addons, get_addon_route


logger = get_logger(__name__)


def mount_core_routes(app) -> None:
    logger.info("Mounting core routes...")

    router_main.to_app(app)
    router_auth.to_app(app)
    router_oauth.to_app(app)
    router_editor.to_app(app)
    router_admin_sites.to_app(app)
    router_admin_users.to_app(app)
    router_admin_roles.to_app(app)
    router_settings.to_app(app)
    router_profile.to_app(app)
    router_cart.to_app(app)

    logger.info(
        "✓ Core routes mounted (main, auth, oauth, editor, admin_sites, admin_users, admin_roles, settings, profile, cart)"
    )


def _mount_domain_router(app, domain: str) -> None:
    route_prefix = get_addon_route(domain)

    if domain == "blog":
        from add_ons.domains.blog import router_blog

        router_blog.to_app(app)
        return

    if domain == "commerce":
        from add_ons.domains.commerce import router_commerce

        router_commerce.to_app(app)
        return

    if domain == "lms":
        from add_ons.domains.lms import router_lms

        app.mount(route_prefix, router_lms)
        return

    if domain == "social":
        from add_ons.domains.social.routes import router_social

        router_social.to_app(app)
        return

    if domain == "stream":
        from add_ons.domains.stream.routes import router_stream

        router_stream.to_app(app)
        return

    raise ValueError(f"Unsupported domain: {domain}")


def mount_addons(app, *, demo: bool) -> None:
    logger.info("Loading domain add-ons...")

    loader = get_addon_loader()

    loader.load_addon("blog")

    if not demo:
        for domain in get_enabled_addons():
            if domain == "blog":
                continue
            loader.load_addon(domain)

    logger.info("Mounting domain add-on routes...")

    try:
        _mount_domain_router(app, "blog")
        logger.info("✓ Blog add-on mounted")
    except Exception as e:
        logger.error(f"Failed to mount blog add-on: {e}")

    if demo:
        return

    for domain in get_enabled_addons():
        if domain == "blog":
            continue
        try:
            _mount_domain_router(app, domain)
            logger.info(f"✓ {domain} add-on mounted")
        except Exception as e:
            logger.warning(f"⚠️ Failed to mount add-on {domain}: {e}")


def mount_example_apps(app, services: dict, *, demo: bool) -> None:
    if not demo:
        logger.info("ℹ️  Example applications skipped (demo mode disabled)")
        return

    logger.info("Mounting example applications...")

    auth_service = services["auth_service"]
    user_service = services["user_service"]
    postgres = services["postgres"]
    mongodb = services["mongodb"]
    redis = services["redis"]

    from examples.eshop import create_eshop_app
    from examples.lms import create_lms_app
    from examples.social import create_social_app
    from examples.streaming import create_streaming_app

    try:
        eshop_app = create_eshop_app(
            auth_service=auth_service,
            user_service=user_service,
            postgres=postgres,
            mongodb=mongodb,
            redis=redis,
            demo=demo,
        )
        app.mount("/eshop-example", eshop_app)
        logger.info(f"✓ E-Shop example mounted at /eshop-example (demo={demo})")
    except Exception as e:
        logger.error(f"Failed to mount e-shop example: {e}")
        logger.exception(e)

    try:
        lms_app = create_lms_app(
            auth_service=auth_service,
            user_service=user_service,
            postgres=postgres,
            mongodb=mongodb,
            redis=redis,
            demo=demo,
        )
        app.mount("/lms-example", lms_app)
        logger.info(f"✓ LMS example mounted at /lms-example (demo={demo})")
    except Exception as e:
        logger.error(f"Failed to mount LMS example: {e}")
        logger.exception(e)

    try:
        social_app = create_social_app(
            auth_service=auth_service,
            user_service=user_service,
            postgres=postgres,
            mongodb=mongodb,
            redis=redis,
            demo=demo,
        )
        app.mount("/social-example", social_app)
        logger.info(f"✓ Social example mounted at /social-example (demo={demo})")
    except Exception as e:
        logger.error(f"Failed to mount social example: {e}")
        logger.exception(e)

    try:
        streaming_app = create_streaming_app(
            auth_service=auth_service,
            user_service=user_service,
            postgres=postgres,
            mongodb=mongodb,
            redis=redis,
            demo=demo,
        )
        app.mount("/streaming-example", streaming_app)
        logger.info(f"✓ Streaming example mounted at /streaming-example (demo={demo})")
    except Exception as e:
        logger.error(f"Failed to mount streaming example: {e}")
        logger.exception(e)


def mount_all(app, services: dict, *, demo: bool) -> None:
    mount_core_routes(app)
    mount_addons(app, demo=demo)
    mount_example_apps(app, services, demo=demo)
