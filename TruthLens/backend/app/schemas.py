from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


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
    source_type: Optional[str] = None
    source_trust_level: Optional[str] = None
    language: Optional[str] = None
    batch_label: Optional[str] = None


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class DomainAnalysis(BaseModel):
    domain: str
    trust_level: str
    source_type: str
    region: str


class AnalyzeResponse(BaseModel):
    credibility_score: int
    credibility_label: str
    explanation: str
    risk_signals: List[str]
    confidence_note: str
    verification_tips: List[str]
    domain_analysis: DomainAnalysis


class TrendingTopic(BaseModel):
    topic: str
    region: str
    intensity: int
    article_count: int
    freshness: str
    credibility_warning: bool


class RefreshLog(BaseModel):
    batch_label: str
    started_at: str
    finished_at: str
    inserted_count: int
    duplicate_count: int
    failed_source_count: int
    trend_update_count: int


class OverviewStats(BaseModel):
    total_articles: int
    morocco_articles: int
    world_articles: int
    reliable_count: int
    suspicious_count: int
    last_refresh_batch: Optional[str] = None
    last_refresh_at: Optional[str] = None


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
    article_url: Optional[str] = None
    article_source: Optional[str] = None
    article_region: Optional[str] = None
    risk_signals: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    suggested_checks: List[str] = Field(default_factory=list)
    model: str
    grounded_in_scope: bool = True