from pydantic import BaseModel, EmailStr
from typing import Optional, List


class NewsItem(BaseModel):
    title: str
    source_name: str
    published_at: str
    country: str
    category: str
    url: str
    description: str
    credibility_score: int
    credibility_label: str
    explanation: str


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    credibility_score: int
    credibility_label: str
    explanation: str
    risk_signals: List[str]


class UserRegister(BaseModel):
    full_name: Optional[str] = ""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    full_name: Optional[str] = ""
    email: EmailStr
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic