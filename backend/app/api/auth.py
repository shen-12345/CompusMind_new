from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest, ChangePasswordRequest, UserInfo,
)
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.utils.response import success, error

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.login(req.username, req.password)
        # 记录登录日志
        audit = AuditService(db)
        await audit.log(
            operator_id=result["user"]["user_id"],
            operator_name=result["user"]["name"],
            action="user_login",
            resource_type="users",
            resource_id=result["user"]["user_id"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success(data=result)
    except ValueError as e:
        return error(code=1001, message=str(e))


@router.post("/refresh")
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """刷新 Token"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(req.refresh_token)
        return success(data=result)
    except ValueError as e:
        return error(code=1002, message=str(e))


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success(data=UserInfo.model_validate(current_user).model_dump())


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    try:
        auth_service = AuthService(db)
        await auth_service.change_password(current_user, req.old_password, req.new_password)
        # 记录日志
        audit = AuditService(db)
        await audit.log(
            operator_id=current_user.user_id,
            operator_name=current_user.name,
            action="change_password",
            resource_type="users",
            resource_id=current_user.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success(message="密码修改成功")
    except ValueError as e:
        return error(code=1001, message=str(e))