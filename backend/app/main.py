from fastapi import FastAPI, Depends, Request
import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlsplit

from .db import engine, Base
from .routers import auth, notes, ledger, todos, exports, ai
from .auth import get_current_user
from .config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(title="Xmem API")

cors_origins = [x.strip() for x in (settings.cors_origins or "").split(",") if x.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def is_request_secure(request: Request) -> bool:
    """判断请求是否为 HTTPS（支持反向代理透传的 X-Forwarded-Proto）。"""
    forwarded = request.headers.get("x-forwarded-proto")
    if forwarded:
        proto = forwarded.split(",")[0].strip().lower()
        return proto == "https"
    return request.url.scheme.lower() == "https"


def normalize_origin(value: str | None) -> str | None:
    """规范化 Origin 值，避免因大小写、末尾斜杠等差异导致误判。"""
    if value is None:
        return None

    raw = value.strip()
    if not raw:
        return None

    if raw.lower() == "null":
        return None

    raw = raw.rstrip("/")

    try:
        parsed = urlsplit(raw)
    except Exception:
        return raw

    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    return raw


def get_csrf_trusted_origins() -> set[str]:
    """解析 CSRF 可信 Origin 列表（逗号分隔，支持自动规范化）。"""
    raw = settings.csrf_trusted_origins or ""
    items = [x.strip() for x in raw.split(",")]
    normalized = (normalize_origin(x) for x in items)
    return {x for x in normalized if x}


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """统一处理 HTTPS 强制、CSRF Origin 校验与安全响应头。"""
    trusted = get_csrf_trusted_origins()

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = normalize_origin(request.headers.get("origin"))
        if origin and trusted and origin not in trusted:
            return JSONResponse(status_code=403, content={"detail": "CSRF 校验失败：Origin 不受信任"})

    if (
        request.method == "POST"
        and request.url.path in {"/auth/login", "/auth/register", "/auth/change-password"}
        and not settings.allow_insecure_http
        and not is_request_secure(request)
    ):
        return JSONResponse(status_code=400, content={"detail": "认证请求必须通过 HTTPS 发送"})

    response = await call_next(request)

    if is_request_secure(request):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    return response


@app.on_event("startup")
async def on_startup():
    """启动时确保数据库表结构存在。"""
    if settings.app_env == "test":
        return
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Error creating tables: {e}")



@app.get("/health")
async def health():
    """健康检查接口。"""
    return {"status": "ok"}



app.include_router(auth.router)

app.include_router(notes.public_router)

# 其他notes路由需要认证
app.include_router(exports.router, dependencies=[Depends(get_current_user)])
app.include_router(notes.router, dependencies=[Depends(get_current_user)])

app.include_router(ledger.router, dependencies=[Depends(get_current_user)])
app.include_router(todos.router, dependencies=[Depends(get_current_user)])
app.include_router(ai.router, dependencies=[Depends(get_current_user)])

