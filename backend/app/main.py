import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db
from app.routes.developers import router as developers_router
from app.routes.history import router as history_router
from app.routes.pipeline import router as pipeline_router
from app.routes.providers import router as providers_router
from app.routes.export import router as export_router
from app.routes.projects import router as projects_router
from app.routes.settings import router as settings_router
from app.ws.manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(pipeline_router)
app.include_router(developers_router)
app.include_router(providers_router)
app.include_router(history_router)
app.include_router(settings_router)
app.include_router(projects_router)
app.include_router(export_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
