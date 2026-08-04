from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.response import success

router = APIRouter(prefix="/admin/audit-logs", tags=["审计日志"], dependencies=[Depends(require_roles(["super_admin"]))])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str = None,
    operator_name: str = None,
    resource_type: str = None,
    start_time: str = None,
    end_time: str = None,
    db: AsyncSession = Depends(get_db),
):
    """审计日志列表"""
    service = AuditService(db)
    logs, total = await service.list_logs(
        page=page, page_size=page_size,
        action=action, operator_name=operator_name,
        resource_type=resource_type,
        start_time=start_time, end_time=end_time,
    )
    items = [
        {
            "log_id": log.log_id,
            "operator_id": log.operator_id,
            "operator_name": log.operator_name,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return success(data={"items": items, "total": total, "page": page, "page_size": page_size})