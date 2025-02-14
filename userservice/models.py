from pydantic import BaseModel
from typing import List

class UserFavorites(BaseModel):
    favorites: List[str]
