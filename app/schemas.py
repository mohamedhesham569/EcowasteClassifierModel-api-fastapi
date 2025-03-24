from pydantic import BaseModel,EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

class ClassificationResultCreate(BaseModel):
    class_name: str
    confidence: float
    user_id: int

class ClassificationResult(BaseModel):
    id: int
    class_name: str
    confidence: float
    user_id: int

    class Config:
        orm_mode = True