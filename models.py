from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import uuid
import datetime


VALID_CATEGORIES = [
    "Mobiteli", 
    "Računala i laptopi", 
    "Televizori", 
    "Kuhinjski aparati", 
    "Automobili", 
    "Bicikli", 
    "Odjeća i obuća", 
    "Elektronička oprema", 
    "Zdravlje", 
    "Igračke", 
    "Sportska oprema", 
    "Alati i oprema", 
    "Knjige", 
    "Glazbeni instrumenti"
]

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
    category: str  
    rating: int = Field(ge=1, le=5) 
    tags: List[str] = []
    comment: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    comments: List[dict] = []
    
    @classmethod
    def validate_category(cls, category: str):
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Nevažeća kategorija. Dopuštene kategorije: {', '.join(VALID_CATEGORIES)}")

    def __init__(self, **data):
        super().__init__(**data)
        self.validate_category(self.category) 
    
class Comment(BaseModel):
    username: str
    comment: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    
   