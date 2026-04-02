from pydantic import BaseModel
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