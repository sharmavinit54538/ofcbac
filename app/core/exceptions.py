from typing import Any, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.response import error_response


class APIException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "An internal server error occurred",
        errors: Optional[List[Any]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class AuthenticationError(APIException):
    def __init__(self, message: str = "Authentication failed", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message, errors=errors)


class PermissionDeniedError(APIException):
    def __init__(self, message: str = "Permission denied", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message, errors=errors)


class NotFoundError(APIException):
    def __init__(self, message: str = "Resource not found", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, errors=errors)


class ConflictError(APIException):
    def __init__(self, message: str = "Resource conflict", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, errors=errors)


class ValidationError(APIException):
    def __init__(self, message: str = "Validation failed", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, errors=errors)


class RateLimitError(APIException):
    def __init__(self, message: str = "Rate limit exceeded", errors: Optional[List[Any]] = None):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, message=message, errors=errors)


def register_exception_handlers(app):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message=exc.message, errors=exc.errors, request_id=request_id)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        formatted_errors = []
        for error in exc.errors():
            formatted_errors.append({
                "field": " -> ".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error")
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Validation failed for request parameters",
                errors=formatted_errors,
                request_id=request_id
            )
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=str(exc.detail),
                errors=[],
                request_id=request_id
            )
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                message="An unexpected internal server error occurred",
                errors=[str(exc)],
                request_id=request_id
            )
        )
