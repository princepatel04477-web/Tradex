"""Tradly API Gateway & Lifespan Entrypoint (TRADLY_SRS v1.0)."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import time
import uuid
from typing import AsyncGenerator
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.routers import ai, alerts, analysis, auth, market, strategy, trading
from app.core.config import settings
from app.core.envelope import ApiResponse
from app.core.errors import TradlyException
from app.core.logging import logger, set_correlation_id
from app.core.rate_limit import RateLimitMiddleware
from app.repositories.base import close_db_pool, init_db_pool, get_db_pool
from app.services.alert_service import alert_service
from app.services.market_service import market_service
from app.services.trading_service import trading_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    await init_db_pool()
    yield
    logger.info("Shutting down Tradly API...")
    await close_db_pool()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform API Gateway",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 1. Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Root & Health Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "service": "Tradly Forex Intelligence API Gateway",
        "status": "healthy",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_v1": "/api/v1",
    }


@app.get("/health", response_model=ApiResponse[dict])
async def health_check() -> ApiResponse[dict]:
    return ApiResponse.success({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if get_db_pool() else "in_memory_fallback",
        "market_provider": settings.MARKET_DATA_PROVIDER,
    })


# ---------------------------------------------------------------------------
# Middleware: Security Headers, Request Tracing, and CORS
# ---------------------------------------------------------------------------
@app.middleware("http")
async def correlation_and_security_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_correlation_id(corr_id)
    start_time = time.perf_counter()

    response = await call_next(request)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = corr_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Server-Timing"] = f"total;dur={latency_ms}"

    return response


# 3. Global Exception Handlers (Guaranteeing Envelope Law)
@app.exception_handler(TradlyException)
async def tradly_exception_handler(request: Request, exc: TradlyException):
    logger.warning(f"Domain exception on {request.url.path}: {exc.code} - {exc.message}")
    envelope = ApiResponse.fail(code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    envelope = ApiResponse.fail(code="VALIDATION_ERROR", message="Invalid request parameters", details=errors)
    return JSONResponse(status_code=422, content=envelope.model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    envelope = ApiResponse.fail(code=f"HTTP_{exc.status_code}", message=str(exc.detail))
    content = envelope.model_dump()
    content["detail"] = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    envelope = ApiResponse.fail(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred.")
    return JSONResponse(status_code=500, content=envelope.model_dump())


# 4. Include Routers
API_V1_PREFIX = "/api/v1"
app.include_router(market.router, prefix=API_V1_PREFIX)
app.include_router(analysis.router, prefix=API_V1_PREFIX)
app.include_router(trading.router, prefix=API_V1_PREFIX)
app.include_router(ai.router, prefix=API_V1_PREFIX)
app.include_router(alerts.router, prefix=API_V1_PREFIX)
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(strategy.router, prefix=API_V1_PREFIX)


# 5. Root & Healthcheck Endpoints
@app.get("/health", response_model=ApiResponse[dict])
async def health_check() -> ApiResponse[dict]:
    return ApiResponse.success({
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    })


# 6. Real-time WebSocket Stream for Live Ticks, Margin Recalculation & Alert Triggers
@app.websocket("/api/v1/ws/stream")
async def websocket_market_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected to live market stream")
    try:
        while True:
            # 1. Update ticks
            ticks = market_service.update_ticks()
            # 2. Update paper trading positions
            trading_service.update_positions_on_tick()
            # 3. Check price alerts
            alert_events = await alert_service.check_alerts_on_tick()

            payload = {
                "type": "market_tick",
                "ticks": {k: t.model_dump() for k, t in ticks.items()},
                "sessions": market_service.get_market_sessions().model_dump(),
                "account": trading_service.get_account().model_dump(),
                "alert_events": [e.model_dump() for e in alert_events],
            }
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
