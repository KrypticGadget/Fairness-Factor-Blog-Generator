# database/models.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    role: str = Field(default="user", description="User's role (user or admin)")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(default=None)
    status: str = Field(default="active")

    class Config:
        from_attributes = True

class Session(BaseModel):
    user_email: EmailStr
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    active: bool = True

    class Config:
        from_attributes = True

class AuditLog(BaseModel):
    user_email: EmailStr
    action: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[dict] = None

    class Config:
        from_attributes = True