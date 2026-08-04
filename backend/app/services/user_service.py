from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.core.security import hash_password
from app.schemas.user import CreateUserRequest, UpdateUserRequest


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: CreateUserRequest) -> User:
        """创建单个用户"""
        # 检查用户名是否已存在
        result = await self.db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        # 初始密码：school_id + "@Abc" 或 "123456@Abc"
        default_password = f"{data.school_id or data.username}@Abc"
        user = User(
            username=data.username,
            password_hash=hash_password(default_password),
            name=data.name,
            role=data.role,
            department=data.department,
            education_level=data.education_level,
            grade=data.grade,
            admin_scope=data.admin_scope,
            school_id=data.school_id,
            email=data.email,
            is_first_login=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user, default_password

    async def list_users(
        self, page: int = 1, page_size: int = 20,
        keyword: Optional[str] = None, role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """用户列表（分页+搜索+筛选）"""
        query = select(User)
        count_query = select(func.count(User.user_id))

        if keyword:
            keyword_filter = or_(
                User.username.ilike(f"%{keyword}%"),
                User.name.ilike(f"%{keyword}%"),
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)
        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def get_user(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, data: UpdateUserRequest) -> User:
        user = await self.get_user(user_id)
        if user is None:
            raise ValueError("用户不存在")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def toggle_active(self, user_id: int) -> User:
        user = await self.get_user(user_id)
        if user is None:
            raise ValueError("用户不存在")
        user.is_active = not user.is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def batch_import(self, users_data: list[dict]) -> dict:
        """批量导入学生"""
        success = 0
        failures = []
        for row, data in enumerate(users_data, start=2):  # row 从 2 开始（Excel 表头占第 1 行）
            try:
                username = data.get("username", "").strip()
                if not username:
                    failures.append({"row": row, "reason": "用户名为空"})
                    continue
                # 检查是否重复
                result = await self.db.execute(select(User).where(User.username == username))
                if result.scalar_one_or_none():
                    failures.append({"row": row, "reason": "用户名重复"})
                    continue
                default_password = f"{username}@Abc"
                user = User(
                    username=username,
                    password_hash=hash_password(default_password),
                    name=data.get("name", "").strip(),
                    role="student",
                    department=data.get("department", "").strip(),
                    education_level=data.get("education_level", "").strip() or None,
                    grade=data.get("grade", "").strip() or None,
                    school_id=data.get("school_id", "").strip() or None,
                    email=data.get("email", "").strip() or None,
                    is_first_login=True,
                )
                self.db.add(user)
                success += 1
            except Exception as e:
                failures.append({"row": row, "reason": str(e)})
        await self.db.commit()
        return {"total": len(users_data), "success": success, "failures": failures}