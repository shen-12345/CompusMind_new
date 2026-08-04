"""种子数据脚本：创建默认超级管理员账号"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import async_session, engine, Base
from app.core.security import hash_password
from app.models.user import User


async def seed():
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 检查是否已有超级管理员
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.role == "super_admin"))
        if result.scalar_one_or_none():
            print("超级管理员已存在，跳过创建")
            return

        # 创建默认超级管理员
        admin = User(
            username="admin",
            password_hash=hash_password("Admin@123"),
            name="超级管理员",
            role="super_admin",
            department="系统管理部",
            is_first_login=True,
        )
        session.add(admin)
        await session.commit()
        print("[OK] 默认超级管理员创建成功")
        print(f"    用户名：admin")
        print(f"    密码：Admin@123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())