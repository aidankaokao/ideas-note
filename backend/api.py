import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.engine import engine
from db.tables import metadata, run_light_migrations
from routers import agent, auth, mentor, mindmaps, notes, providers, topics, users
from services.auth_service import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)  # SQLite 檔與執行期產物放 data/
    metadata.create_all(engine)
    run_light_migrations(engine)  # 舊庫補新欄位
    seed_admin()  # 無任何使用者時建立預設 admin/admin
    yield


app = FastAPI(title="ideas-note", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發期放寬；正式走 nginx 同源反代不需 CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── 正式部署（Cloud Run 單一容器）：backend/static/ 存在時，由 FastAPI 直接伺服前端 build ──
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_STATIC_DIR):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")),
        name="assets",
    )

    # SPA fallback：/api 路由已先註冊會優先匹配；其餘路徑回 index.html（前端路由重整不 404）
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = os.path.join(_STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(mentor.router, prefix="/api")
app.include_router(mindmaps.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    # 本機/一般容器維持 8000（backend-conventions.md §3）；Cloud Run 會注入 PORT=8080
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
