from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, resume, state
from app.dependencies import get_graph
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # warm up graph saat startup supaya request pertama tidak lambat
    get_graph()
    yield


app = FastAPI(
    title="AI Agent App",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — sesuaikan origins dengan NestJS backend-mu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(resume.router)
app.include_router(state.router)


@app.get("/health")
async def health():
    return {"status": "ok"}