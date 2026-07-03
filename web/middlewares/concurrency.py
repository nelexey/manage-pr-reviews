import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class ConcurrencyLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_concurrent_requests: int = 100):
        super().__init__(app)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def dispatch(self, request: Request, call_next):
        try:
            # Ждем максимум 2 секунды, если сервер перегружен
            await asyncio.wait_for(self.semaphore.acquire(), timeout=2.0)
            try:
                response = await call_next(request)
                return response
            finally:
                self.semaphore.release()
        except TimeoutError:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "TOO_MANY_REQUESTS",
                        "message": "Сервер перегружен, попробуйте позже.",
                    }
                },
            )
