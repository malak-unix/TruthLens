from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class NewsItem(BaseModel):
    title: str
    source_name: str
    published_at: str
    fetched_at: Optional[str] = None
    analyzed_at: Optional[str] = None
    country: str
    category: str
    url: str
    image_url: Optional[str] = None
    description: str
    credibility_score: int
    credibility_label: str
    explanation: str
    source_type: Optional[str] = None
    source_trust_level: Optional[str] = None
    language: Optional[str] = None
    batch_label: Optional[str] = None
    provider_name: Optional[str] = None
    source_domain: Optional[str] = None
    priority_topic: Optional[str] = None
    priority_score: Optional[float] = None
    trend_score: Optional[float] = None
    coverage_score: Optional[float] = None
    ranking_score: Optional[float] = None
    is_priority: Optional[bool] = None
    is_conflict: Optional[bool] = None
    source_score: Optional[int] = None
    article_score: Optional[int] = None
    corroboration_score: Optional[int] = None
    verification_status: Optional[str] = None


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class DomainAnalysis(BaseModel):
    domain: str
    trust_level: str
    source_type: str
    region: str


class SourceProfile(BaseModel):
    source_name: str
    domain: str
    country: str
    region: str
    language: str
    source_type: str
    base_reliability_score: int
    transparency_signals: List[str] = Field(default_factory=list)
    corrections_policy_known: bool
    ownership_known: bool
    byline_practice_known: bool
    fact_checker_flag: bool
    external_reference: str
    risk_tier: str
    review_notes: str
    trust_level: str


class AnalyzeResponse(BaseModel):
    credibility_score: int
    credibility_label: str
    source_score: int
    article_score: int
    corroboration_score: int
    final_score: int
    final_label: str
    verification_status: str
    explanation: str
    risk_signals: List[str]
    confidence_note: str
    verification_tips: List[str]
    domain_analysis: DomainAnalysis
    source_profile: SourceProfile


class TrendingTopic(BaseModel):
    topic: str
    title: Optional[str] = None
    normalized_topic: Optional[str] = None
    region: str
    intensity: int
    article_count: int
    freshness: str
    credibility_warning: bool
    source_signals: List[str] = Field(default_factory=list)
    platform_signals: List[str] = Field(default_factory=list)
    related_articles_count: int = 0
    recency_score: float = 0
    virality_score: float = 0
    verification_score: float = 0
    verification_gap_score: float = 0
    freshness_label: Optional[str] = None
    confidence_note: Optional[str] = None


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
    selected_trend_title: Optional[str] = None
    selected_trend_region: Optional[str] = None
    selected_trend_freshness: Optional[str] = None
    selected_trend_confidence_note: Optional[str] = None
    selected_trend_source_signals: List[str] = Field(default_factory=list)
    selected_trend_platform_signals: List[str] = Field(default_factory=list)
    selected_trend_related_articles_count: Optional[int] = None
    selected_trend_verification_gap_score: Optional[float] = None
    region_focus: Optional[str] = None
    active_view: Optional[str] = None
    morocco_trends: List[str] = Field(default_factory=list)
    world_trends: List[str] = Field(default_factory=list)
    history: List[dict] = Field(default_factory=list)


class AssistantAnalysisSnapshot(BaseModel):
    input_type: str
    credibility_score: int
    credibility_label: str
    source_score: int
    article_score: int
    corroboration_score: int
    final_score: int
    final_label: str
    verification_status: str
    explanation: str
    risk_signals: List[str] = Field(default_factory=list)
    verification_tips: List[str] = Field(default_factory=list)
    source_profile: Optional[SourceProfile] = None


class ChatResponse(BaseModel):
    answer: str
    suggested_checks: List[str] = Field(default_factory=list)
    model: str
    grounded_in_scope: bool = True
    intent: str = "general_guidance"
    context_note: Optional[str] = None
    quick_actions: List[str] = Field(default_factory=list)
    analysis_snapshot: Optional[AssistantAnalysisSnapshot] = None
