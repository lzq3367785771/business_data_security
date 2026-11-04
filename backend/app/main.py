from uuid import uuid4

from fastapi import (
    FastAPI,
    Request,
    HTTPException
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.responses import success

from app.modules.auth.router import router as auth_router
from app.modules.customers.router import router as customer_router
from app.modules.policy.router import router as policy_router
from app.modules.audit.router import router as audit_router
from app.modules.systems.router import (
    router as systems_router,
)
from app.modules.data_sources.router import (
    router as data_sources_router,
)
from app.modules.credentials.router import (
    router as credentials_router,
)
from app.modules.assets.router import (
    router as assets_router,
)
from app.modules.sensitive_detection.router import (
    router as sensitive_detection_router,
)
from app.modules.data_access.router import (
    router as data_access_router,
)
from app.modules.access_monitoring.router import (
    router as access_monitoring_router,
)
from app.modules.dashboard.router import (
    router as dashboard_router,
)

from app.modules.file_security.router import (
    router as file_security_router,
)

from app.modules.file_masking.router import (
    router as file_masking_router,
)


app = FastAPI(
    title="Business Data AI Security Platform",
    description="业务数据AI管控与溯源平台",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID"
    ],

    expose_headers=[
        "Content-Disposition",
        "X-Original-SHA256",
        "X-File-SHA256",
        "X-Request-ID",
    ],

)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = (
        request.state.request_id
    )

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):

    detail = exc.detail


    # =========================
    # 结构化业务异常
    # =========================

    if isinstance(
        detail,
        dict,
    ):

        message = (
            detail.get("message")
            or "请求失败"
        )

        data = {
            key: value
            for key, value
            in detail.items()
            if key != "message"
        }

        if not data:
            data = None


    # =========================
    # 普通字符串异常
    # =========================

    else:

        message = str(detail)

        data = None


    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code":
                exc.status_code,

            "message":
                message,

            "data":
                data,

            "request_id":
                getattr(
                    request.state,
                    "request_id",
                    None,
                ),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求参数不合法",
            "data": None,
            "request_id": getattr(
                request.state, "request_id", None
            )
        }
    )


app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(policy_router)
app.include_router(audit_router)
app.include_router(systems_router)
app.include_router(data_sources_router)
app.include_router(credentials_router)
app.include_router(assets_router)
app.include_router(sensitive_detection_router)
app.include_router(data_access_router)
app.include_router(access_monitoring_router)
app.include_router(dashboard_router)
app.include_router(file_security_router)
app.include_router(file_masking_router)


@app.get("/api/v1/health", tags=["System"])
def health(request: Request):
    return success(
        request,
        {"status": "ok"}
    )