from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
import datetime

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str
    
class Review(BaseModel):
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str 
    product_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  
    product_name: str  
    rating: int = Field(ge=1, le=5) 
    comment: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())