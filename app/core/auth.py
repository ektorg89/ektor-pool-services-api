from pydantic import BaseModel, Field, EmailStr

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=60)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserOut(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}
