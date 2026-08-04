from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self, operator_id: int, operator_name: str, action: str,
        resource_type: str, resource_id: Optional[int] = None,
        detail: Optional[dict] = None,
        ip_address: Optional[str] = None, user_agent: Optional[str] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            operator_id=operator_id,
            operator_name=operator_name,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        await self.db.commit()
        return audit_log

    async def list_logs(
        self, page: int = 1, page_size: int = 20,
        action: Optional[str] = None, operator_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[str] = None, end_time: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.log_id))

        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if operator_name:
            query = query.where(AuditLog.operator_name.ilike(f"%{operator_name}%"))
            count_query = count_query.where(AuditLog.operator_name.ilike(f"%{operator_name}%"))
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        if start_time:
            query = query.where(AuditLog.created_at >= start_time)
            count_query = count_query.where(AuditLog.created_at >= start_time)
        if end_time:
            query = query.where(AuditLog.created_at <= end_time)
            count_query = count_query.where(AuditLog.created_at <= end_time)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return list(logs), total