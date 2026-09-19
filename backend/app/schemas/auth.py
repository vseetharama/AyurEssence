from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "patient"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str