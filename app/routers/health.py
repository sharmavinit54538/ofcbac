from fastapi import APIRouter, Request
from app.core.response import success_response

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(request: Request):
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"status": "healthy", "service": "OFC HR Backend API"},
        message="Service is operational.",
        request_id=request_id
    )
