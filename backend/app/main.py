from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import close_mongodb_connection, close_redis_connection
from app.routers.data import router as data_router
from app.routers import auth
from app.routers.reports import router as reports_router
from app.routers.training import router as training_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_mongodb_connection()
    await close_redis_connection()


app = FastAPI(
    title="FastAPI Application",
    description="FastAPI backend with MongoDB and Redis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Application"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(data_router)
app.include_router(reports_router)
app.include_router(training_router)
