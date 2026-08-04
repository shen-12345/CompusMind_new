from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^\\d+$")
    name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(..., pattern="^(super_admin|admin|teacher|student)$")
    department: str = Field(..., max_length=100)
    education_level: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=10)
    admin_scope: Optional[str] = Field(None, max_length=100)
    school_id: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100, pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    education_level: Optional[str] = Field(None, max_length=10)
    grade: Optional[str] = Field(None, max_length=10)
    admin_scope: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100, pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")


class UserResponse(BaseModel):
    user_id: int
    username: str
    name: str
    role: str
    department: str
    education_level: Optional[str] = None
    grade: Optional[str] = None
    admin_scope: Optional[str] = None
    school_id: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    is_first_login: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]


class ImportResult(BaseModel):
    total: int
    success: int
    failures: list[dict]


class ImportPreview(BaseModel):
    total: int
    preview: list[dict]
    headers: list[str]