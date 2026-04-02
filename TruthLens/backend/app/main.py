from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.mock_news import mock_news
from app.schemas import AnalyzeRequest
from app.analyzer import analyze_text_content

app = FastAPI(title="TruthLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "TruthLens backend is running"}


@app.get("/news")
def get_news(country: str | None = None, category: str | None = None):
    results = mock_news

    if country:
        results = [item for item in results if item["country"].lower() == country.lower()]

    if category:
        results = [item for item in results if item["category"].lower() == category.lower()]

    return results


@app.get("/categories")
def get_categories():
    categories = sorted(list(set(item["category"] for item in mock_news)))
    return categories


@app.post("/analyze")
def analyze_content(payload: AnalyzeRequest):
    content = payload.text or payload.url or ""
    return analyze_text_content(content)