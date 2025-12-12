"""
Error Handler Middleware

Centralized error handling for consistent API responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import traceback

from core.exceptions import AppException
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle all exceptions consistently.
    
    Converts custom AppException instances to proper JSON responses.
    Handles unexpected exceptions with proper logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
            
        except AppException as exc:
            # Handle our custom exceptions
            logger.warning(
                f"{exc.__class__.__name__}: {exc.message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                    "details": exc.details
                }
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )
            
        except ValueError as exc:
            # Handle validation errors from Pydantic or other sources
            logger.warning(f"ValueError: {str(exc)}", extra={"path": request.url.path})
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "ValidationError",
                    "message": str(exc),
                    "status_code": 422
                }
            )
            
        except Exception as exc:
            # Handle unexpected exceptions
            logger.error(
                f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "status_code": 500
                }
            )


def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """
    Exception handler for FastAPI exception handlers.
    
    Usage:
        from fastapi import FastAPI
        from core.exceptions import AppException
        from core.middleware.error_handler import handle_app_exception
        
        app = FastAPI()
        app.add_exception_handler(AppException, handle_app_exception)
    """
    logger.warning(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )
