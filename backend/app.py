"""
app.py — FastAPI application factory.

Cloud concepts wired here:
  * CORS allowlist  (browser security between SPA and API)
  * request logging (observability -> feeds Render/CloudWatch logs)
  * rate limiting   (abuse protection, like an API gateway)
  * error handlers  (graceful failure responses)
  * routers         (the REST API surface)
  * DB bootstrap    (create tables on startup for local/demo use)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.middleware.error_handlers import register_error_handlers
from backend.middleware.logging_middleware import RequestLoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.routes.auth_routes import router as auth_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.diet_routes import router as diet_router
from backend.routes.file_routes import router as file_router
from backend.routes.health_routes import router as health_router
from backend.routes.plan_routes import router as plan_router
from backend.routes.profile_routes import router as profile_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("diet.app")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "REST API for the AI-Powered Personal Diet Planner with Cloud "
            "Storage — JWT auth, AI meal-plan generation with rule-based "
            "fallback, cloud database and object storage."
        ),
    )

    # ---- CORS: only origins in the allowlist may call this API ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Observability + protection middleware ----
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # ---- Error handling ----
    register_error_handlers(app)

    # ---- REST API routers ----
    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(diet_router)
    app.include_router(plan_router)
    app.include_router(file_router)
    app.include_router(dashboard_router)
    app.include_router(health_router)

    # ---- Create tables on startup (local/demo convenience) ----
    @app.on_event("startup")
    def _bootstrap() -> None:
        from backend.database import Base, engine
        import backend.models  # noqa: F401 — register all models

        Base.metadata.create_all(bind=engine)
        logger.info(
            "Diet planner API started | env=%s | storage=%s | auth=%s | db=%s | ai=%s",
            settings.ENVIRONMENT,
            settings.STORAGE_PROVIDER,
            settings.AUTH_PROVIDER,
            settings.DATABASE_URL.split("://")[0],
            settings.AI_PROVIDER,
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
