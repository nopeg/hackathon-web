from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    accessToken: str
    tokenType: str

class TokenData(BaseModel):
    username: Optional[str] = None