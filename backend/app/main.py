from fastapi import FastAPI, Depends, HTTPException  
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import FileResponse
from pathlib import Path

from .db import engine, Base
from .routers import auth, notes, ledger, todos
from .auth import get_current_user

app = FastAPI(title="Xmem API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

# 文件获取端点不需要认证（公开访问）
UPLOAD_DIR = Path("uploads")
IMAGE_DIR = UPLOAD_DIR / "images"
FILE_DIR = UPLOAD_DIR / "files"

@app.get("/notes/files/{file_type}/{file_name}")
async def get_file(file_type: str, file_name: str):
    """获取上传的文件（公开访问，不需要认证）"""
    if file_type == "images":
        file_path = IMAGE_DIR / file_name
    elif file_type == "files":
        file_path = FILE_DIR / file_name
    else:
        raise HTTPException(status_code=404, detail="文件类型错误")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(file_path)

# 其他notes路由需要认证
app.include_router(notes.router, dependencies=[Depends(get_current_user)])

app.include_router(ledger.router, dependencies=[Depends(get_current_user)])
app.include_router(todos.router, dependencies=[Depends(get_current_user)])

