from pydantic import BaseModel
from typing import Optional, Any

class MessageResponse(BaseModel):
    message: str
    data: Optional[Any] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
