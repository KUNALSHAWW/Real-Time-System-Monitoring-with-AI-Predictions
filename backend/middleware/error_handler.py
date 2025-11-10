"""
Global error handler middleware
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from core.logger import get_logger

logger = get_logger("error_handler")


async def error_handler_middleware(request: Request, call_next):
    """Handle errors globally"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(
            f"Unhandled error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_type": type(e).__name__
            }
        )
