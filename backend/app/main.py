from fastapi import FastAPI, Depends  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]

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
app.include_router(notes.router, dependencies=[Depends(get_current_user)])
app.include_router(ledger.router, dependencies=[Depends(get_current_user)])
app.include_router(todos.router, dependencies=[Depends(get_current_user)])

