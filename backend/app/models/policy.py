from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content_full = Column(Text, nullable=False)
    department = Column(String(100), nullable=False)
    education_level = Column(String(10), nullable=False)  # 本科, 硕士, 博士, 全校
    applicable_grades = Column(JSONB, nullable=False)  # ["2023","2024"]
    project_category = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    version = Column(Integer, default=1)
    file_md5 = Column(String(64), nullable=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Policy {self.title}>"


class PolicyMetadata(Base):
    __tablename__ = "policy_metadata"

    metadata_id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), unique=True, nullable=False)
    project_name = Column(String(200), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    prerequisites = Column(JSONB, nullable=True)  # 硬性门槛数组
    mutually_exclusive = Column(JSONB, nullable=True)  # 互斥项数组
    material_list = Column(JSONB, nullable=False)  # 材料清单数组
    review_process = Column(Text, nullable=True)  # 评选流程说明
    contact_info = Column(String(200), nullable=True)  # 联系方式
    confidence_score = Column(String(10), nullable=True)  # LLM 置信度，如 "0.85"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PolicyMetadata {self.project_name}>"


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    chunk_content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_title = Column(String(200), nullable=True)  # 段落标题（如章节名）
    embedding = Column(Vector(1024), nullable=True)  # 向量嵌入（通义千问 1024维）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PolicyChunk {self.policy_id}:{self.chunk_index}>"