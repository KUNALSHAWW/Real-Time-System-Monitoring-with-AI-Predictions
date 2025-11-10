"""
Logging middleware for request/response tracking
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.logger import get_logger

logger = get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""

    async def dispatch(self, request: Request, call_next):
        request_start_time = time.time()

        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
            },
        )

        response = await call_next(request)

        process_time = time.time() - request_start_time

        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            },
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response
