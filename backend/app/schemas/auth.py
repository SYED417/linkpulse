from pydantic import BaseModel, EmailStr


# Request body for registration.
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# Response from the /token login endpoint.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
