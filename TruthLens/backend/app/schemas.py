from pydantic import BaseModel, EmailStr, Field
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


class ChatRequest(BaseModel):
    message: str
    article_title: Optional[str] = None
    article_summary: Optional[str] = None
    article_score: Optional[int] = None
    article_label: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    suggested_checks: List[str] = Field(default_factory=list)
    model: str
    grounded_in_scope: bool = True
