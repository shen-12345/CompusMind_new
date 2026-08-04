from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PolicyResponse(BaseModel):
    policy_id: int
    title: str
    department: str
    education_level: str
    applicable_grades: list
    project_category: str
    status: str
    version: int
    created_by: int
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PolicyMetadataResponse(BaseModel):
    metadata_id: int
    policy_id: int
    project_name: str
    deadline: Optional[datetime] = None
    prerequisites: Optional[list] = None
    mutually_exclusive: Optional[list] = None
    material_list: Optional[list] = None
    review_process: Optional[str] = None
    contact_info: Optional[str] = None
    confidence_score: Optional[str] = None

    model_config = {"from_attributes": True}


class PolicyDetailResponse(BaseModel):
    policy: PolicyResponse
    metadata: Optional[PolicyMetadataResponse] = None


class PolicyListResponse(BaseModel):
    total: int
    items: list[PolicyResponse]


class UploadResponse(BaseModel):
    policy_id: int
    title: str
    status: str
    message: str