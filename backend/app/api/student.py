from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.policy_service import PolicyService
from app.schemas.policy import PolicyResponse
from app.utils.response import success, error

router = APIRouter(prefix="/student", tags=["学生端"])


@router.get("/policies")
async def get_student_policies(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学生可见的政策列表"""
    if current_user.role != "student":
        return error(message="仅学生可访问")

    service = PolicyService(db)
    policies, total = await service.get_student_policies(
        student_department=current_user.department,
        student_education=current_user.education_level or "本科",
        student_grade=current_user.grade or "2024",
        page=page,
        page_size=page_size,
    )
    items = [PolicyResponse.model_validate(p).model_dump(mode="json") for p in policies]
    return success(data={"items": items, "total": total, "page": page, "page_size": page_size})