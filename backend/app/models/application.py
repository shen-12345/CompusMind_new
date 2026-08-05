from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class UserApplication(Base):
    """学生申请记录"""
    __tablename__ = "user_applications"

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    status = Column(String(20), nullable=False, default="preparing")
    # preparing, submitted, pending_review, needs_revision,
    #初审通过, pending_final, pending_admin, completed, abandoned

    applied_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    paper_submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    feedback = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<App {self.user_id}-{self.policy_id} [{self.status}]>"


class ApplicationMaterial(Base):
    """申请材料"""
    __tablename__ = "application_materials"

    material_id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("user_applications.application_id"), nullable=False)
    material_name = Column(String(100), nullable=False)
    file_name = Column(String(200), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    upload_status = Column(String(20), default="not_uploaded")
    # not_uploaded, uploaded
    reject_reason = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Material {self.material_name} [{self.upload_status}]>"