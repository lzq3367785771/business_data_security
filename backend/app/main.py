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


app = FastAPI(
    title="Business Data AI Security Platform",
    description="业务数据AI管控与溯源平台",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID"
    ]
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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
            "request_id": getattr(
                request.state, "request_id", None
            )
        }
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


@app.get("/api/v1/health", tags=["System"])
def health(request: Request):
    return success(
        request,
        {"status": "ok"}
    )