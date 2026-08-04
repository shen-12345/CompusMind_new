from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_roles, get_current_user
from app.models.user import User
from app.services.policy_service import PolicyService
from app.schemas.policy import PolicyResponse, PolicyDetailResponse, PolicyListResponse
from app.services.audit_service import AuditService
from app.utils.response import success, error
from typing import Optional

router = APIRouter(prefix="/policies", tags=["政策管理"])


@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...),
    department: str = Form(...),
    education_level: str = Form(...),
    applicable_grades: str = Form(...),  # JSON 数组字符串
    project_category: str = Form(...),
    request: Request = None,
    current_user: User = Depends(require_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
):
    """上传政策文档"""
    # 校验文件
    if not file.filename.endswith((".pdf", ".docx")):
        return error(message="仅支持 PDF 和 Word 格式")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        return error(message="文件过大，请压缩后上传（最大 20MB）")

    try:
        import json
        grades = json.loads(applicable_grades)
    except json.JSONDecodeError:
        grades = [applicable_grades]

    service = PolicyService(db)
    try:
        result = await service.upload_policy(
            file_content=content,
            filename=file.filename,
            department=department,
            education_level=education_level,
            applicable_grades=grades,
            project_category=project_category,
            created_by=current_user.user_id,
        )

        # 记录审计日志
        audit = AuditService(db)
        await audit.log(
            operator_id=current_user.user_id,
            operator_name=current_user.name,
            action="policy_upload",
            resource_type="policies",
            resource_id=result["policy_id"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return success(data=result)
    except ValueError as e:
        return error(message=str(e))


@router.post("/{policy_id}/extract")
async def extract_metadata(
    policy_id: int,
    current_user: User = Depends(require_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
):
    """调用 LLM 提取结构化字段"""
    service = PolicyService(db)
    detail = await service.get_policy_detail(policy_id)
    if not detail:
        return error(message="政策不存在")

    try:
        result = await service.extract_metadata_with_llm(policy_id, detail["policy"].content_full)
        return success(data=result)
    except ValueError as e:
        return error(message=str(e))


@router.get("")
async def list_policies(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    department: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """政策列表"""
    service = PolicyService(db)

    # 辅导员只能看自己发布的
    created_by = None
    if current_user.role == "teacher":
        created_by = current_user.user_id

    policies, total = await service.get_policy_list(
        page=page, page_size=page_size,
        status=status, department=department,
        created_by=created_by,
    )
    items = [PolicyResponse.model_validate(p).model_dump(mode="json") for p in policies]
    return success(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/{policy_id}")
async def get_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """政策详情"""
    service = PolicyService(db)
    detail = await service.get_policy_detail(policy_id)
    if not detail:
        return error(message="政策不存在")

    policy_data = PolicyResponse.model_validate(detail["policy"]).model_dump(mode="json")
    metadata_data = None
    if detail["metadata"]:
        from app.schemas.policy import PolicyMetadataResponse
        metadata_data = PolicyMetadataResponse.model_validate(detail["metadata"]).model_dump(mode="json")

    return success(data={"policy": policy_data, "metadata": metadata_data})


@router.post("/{policy_id}/publish")
async def publish_policy(
    policy_id: int,
    metadata: dict = {},
    request: Request = None,
    current_user: User = Depends(require_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
):
    """发布政策"""
    service = PolicyService(db)
    try:
        policy = await service.publish_policy(policy_id, metadata)

        audit = AuditService(db)
        await audit.log(
            operator_id=current_user.user_id,
            operator_name=current_user.name,
            action="policy_publish",
            resource_type="policies",
            resource_id=policy_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return success(data=PolicyResponse.model_validate(policy).model_dump(mode="json"))
    except ValueError as e:
        return error(message=str(e))


@router.post("/{policy_id}/withdraw")
async def withdraw_policy(
    policy_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """撤回已发布的政策（恢复为草稿）"""
    service = PolicyService(db)
    try:
        policy = await service.withdraw_policy(policy_id)
        audit = AuditService(db)
        await audit.log(
            operator_id=current_user.user_id,
            operator_name=current_user.name,
            action="policy_withdraw",
            resource_type="policies",
            resource_id=policy_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success(data=PolicyResponse.model_validate(policy).model_dump(mode="json"))
    except ValueError as e:
        return error(message=str(e))


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除草稿政策"""
    service = PolicyService(db)
    try:
        await service.delete_policy(policy_id)
        audit = AuditService(db)
        await audit.log(
            operator_id=current_user.user_id,
            operator_name=current_user.name,
            action="policy_delete",
            resource_type="policies",
            resource_id=policy_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success(message="删除成功")
    except ValueError as e:
        return error(message=str(e))