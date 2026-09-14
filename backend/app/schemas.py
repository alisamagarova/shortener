from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LinkCreateRequest(BaseModel):
    original_url: str = Field(alias="originalUrl")

    model_config = ConfigDict(populate_by_name=True)


class LinkResponse(BaseModel):
    id: int
    short_code: str = Field(alias="shortCode")
    original_url: str = Field(alias="originalUrl")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
