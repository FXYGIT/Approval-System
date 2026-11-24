import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class BusinessError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(message)


def error_response(status: int, code: str, message: str, headers=None):
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}, headers=headers
    )


def install_exception_handlers(app: FastAPI):
    @app.exception_handler(BusinessError)
    async def business_error(request: Request, exc: BusinessError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
        return error_response(exc.status, exc.code, exc.message, headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Pydantic errors can include input (password, token, request body). Never echo them.
        return error_response(422, "VALIDATION_ERROR", "请求参数不合法")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        messages = {
            401: "需要有效的身份凭证",
            403: "无权访问",
            404: "资源不存在",
            405: "请求方法不允许",
            503: "服务暂不可用",
        }
        return error_response(
            exc.status_code,
            f"HTTP_{exc.status_code}",
            messages.get(exc.status_code, "请求失败"),
            exc.headers,
        )

    @app.middleware("http")
    async def unexpected_error_boundary(request: Request, call_next):
        # An Exception handler alone is insufficient: ServerErrorMiddleware re-raises
        # to Uvicorn, which logs the original SQL parameters/exception text.
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001 -- final boundary must sanitize unexpected failures
            logger.error("Unhandled request failure: %s", type(exc).__name__)
            return error_response(500, "INTERNAL_ERROR", "服务内部错误")
