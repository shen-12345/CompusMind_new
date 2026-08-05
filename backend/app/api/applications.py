from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.application_service import ApplicationService
from app.utils.response import success, error

router = APIRouter(prefix="/applications", tags=["申请进度"])


@router.post("/start")
async def start_application(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """开始申请"""
    service = ApplicationService(db)
    try:
        app = await service.start_application(current_user.user_id, policy_id)
        return success(data={"application_id": app.application_id, "status": app.status})
    except ValueError as e:
        return error(message=str(e))


@router.post("/{application_id}/upload")
async def upload_material(
    application_id: int,
    material_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传材料"""
    if not file.filename.endswith((".pdf", ".jpg", ".jpeg", ".png")):
        return error(message="仅支持 PDF、JPG、PNG 格式")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        return error(message="文件过大，最大 5MB")

    service = ApplicationService(db)
    try:
        material = await service.upload_material(
            application_id, material_name, content, file.filename
        )
        return success(data={
            "material_name": material.material_name,
            "file_name": material.file_name,
            "file_size": material.file_size,
            "upload_status": material.upload_status,
        })
    except ValueError as e:
        return error(message=str(e))


@router.delete("/{application_id}/material")
async def delete_material(
    application_id: int,
    material_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除材料"""
    service = ApplicationService(db)
    try:
        await service.delete_material(application_id, material_name)
        return success(message="已删除")
    except ValueError as e:
        return error(message=str(e))


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交电子版"""
    service = ApplicationService(db)
    try:
        app = await service.submit_application(application_id)
        return success(data={"status": app.status})
    except ValueError as e:
        return error(message=str(e))


@router.post("/{application_id}/abandon")
async def abandon_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """放弃申请"""
    service = ApplicationService(db)
    try:
        app = await service.abandon_application(application_id)
        return success(data={"status": app.status})
    except ValueError as e:
        return error(message=str(e))


@router.get("")
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """我的申请列表"""
    service = ApplicationService(db)
    items = await service.get_user_applications(current_user.user_id)
    return success(data=items)


@router.get("/{application_id}")
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """申请详情"""
    service = ApplicationService(db)
    detail = await service.get_application_detail(application_id)
    if not detail:
        return error(message="申请不存在")
    return success(data=detail)