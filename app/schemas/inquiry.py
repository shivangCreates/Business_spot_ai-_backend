
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    company: str | None = Field(default=None, max_length=150)
    project_type: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=10, max_length=5000)

    @field_validator("name", "project_type", "message", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("company", mode="before")
    @classmethod
    def strip_optional_company(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class InquiryResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    company: str | None
    project_type: str
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
