from app.database import BaseModel

class Base(BaseModel):
    __abstract__ = True