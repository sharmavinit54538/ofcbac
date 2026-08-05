import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config.settings import settings
from app.core.response import error_response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Store timestamp logs per IP address: {ip: [timestamps]}
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Bypass CORS preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - 60.0  # 1 minute sliding window

        # Clean old timestamps
        history = [ts for ts in self.request_history[client_ip] if ts > window_start]
        self.request_history[client_ip] = history

        # Differentiate rate limit for auth endpoints vs general routes
        is_auth_route = request.url.path.startswith("/auth") or request.url.path.startswith("/api/v1/auth")
        limit = settings.AUTH_RATE_LIMIT_PER_MINUTE if is_auth_route else settings.RATE_LIMIT_PER_MINUTE

        if len(history) >= limit:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content=error_response(
                    message=f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                    errors=[{"field": "rate_limit", "message": "Too many requests. Please try again later."}],
                    request_id=request_id
                )
            )

        self.request_history[client_ip].append(now)
        return await call_next(request)
