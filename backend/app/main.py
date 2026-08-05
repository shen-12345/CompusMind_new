import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.policies import router as policies_router
from app.api.student import router as student_router
from app.api.agent import router as agent_router
from app.api.applications import router as applications_router
from app.api.admin.users import router as admin_users_router
from app.api.admin.audit_logs import router as admin_audit_logs_router
from app.utils.response import success

# 配置日志为 UTF-8 编码，解决 GBK 无法打印中文的问题
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS 配置（开发阶段允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(policies_router, prefix="/api/v1")
app.include_router(student_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(admin_users_router, prefix="/api/v1")
app.include_router(admin_audit_logs_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/health")
async def api_health_check():
    return {"status": "ok"}