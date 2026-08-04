from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, validate_password_strength,
)
from app.core.config import settings
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """用户登录，返回 Token 和用户信息"""
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError("用户名或密码错误")

        # 检查账号是否被禁用
        if not user.is_active:
            raise ValueError("账号已被禁用，请联系管理员")

        # 检查账号是否被锁定
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
            raise ValueError(f"账号已锁定，请{remaining + 1}分钟后再试")

        # 校验密码
        if not verify_password(password, user.password_hash):
            user.login_attempts += 1
            if user.login_attempts >= settings.LOGIN_LOCK_THRESHOLD:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
            await self.db.commit()
            raise ValueError("用户名或密码错误")

        # 登录成功，重置尝试次数
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()

        # 生成 Token
        token_data = {"user_id": user.user_id, "role": user.role, "department": user.department}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "name": user.name,
                "role": user.role,
                "department": user.department,
                "is_first_login": user.is_first_login,
            },
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """刷新 Access Token"""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Refresh Token 无效或已过期")
        user_id = payload.get("user_id")
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise ValueError("用户不存在或已被禁用")
        token_data = {"user_id": user.user_id, "role": user.role, "department": user.department}
        new_access_token = create_access_token(token_data)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        """修改密码"""
        if not verify_password(old_password, user.password_hash):
            raise ValueError("原密码错误")
        if old_password == new_password:
            raise ValueError("新密码不能与旧密码相同")
        valid, msg = validate_password_strength(new_password)
        if not valid:
            raise ValueError(msg)
        user.password_hash = hash_password(new_password)
        user.is_first_login = False
        await self.db.commit()