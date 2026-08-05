from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[List[Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: Optional[str] = None


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


def error_response(
    message: str = "An error occurred",
    errors: Optional[List[Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }
