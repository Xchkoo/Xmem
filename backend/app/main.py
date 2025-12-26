from fastapi import FastAPI, Depends
import logging

from .db import engine, Base
from .routers import auth, notes, ledger, todos
from .auth import get_current_user

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# FastAPI 会自动从 X-Forwarded-Proto 头识别 HTTPS 请求
# Nginx 已经设置了这些头，所以不需要额外的中间件
app = FastAPI(title="Xmem API")


@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Error creating tables: {e}")



@app.get("/health")
async def health():
    return {"status": "ok"}



app.include_router(auth.router)

# 其他notes路由需要认证
app.include_router(notes.router, dependencies=[Depends(get_current_user)])

app.include_router(ledger.router, dependencies=[Depends(get_current_user)])
app.include_router(todos.router, dependencies=[Depends(get_current_user)])

