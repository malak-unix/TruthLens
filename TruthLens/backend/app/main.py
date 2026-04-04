from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_payload
from app.auth_utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.chat_service import ChatService
from app.config import get_settings
from app.database import (
    create_user,
    get_categories_from_db,
    get_news_from_db,
    get_overview_stats,
    get_refresh_logs,
    get_trending_topics,
    get_user_by_email,
    get_user_by_id,
    init_db,
    save_user_check,
)
from app.ingestion_service import run_ingestion_pipeline
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    NewsItem,
    OverviewStats,
    RefreshLog,
    TokenResponse,
    TrendingTopic,
    UserLogin,
    UserPublic,
    UserRegister,
)
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="TruthLens API",
    description="Backend API for explainable credibility monitoring.",
    version="4.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://192.168.56.1:3000",
        "https://truth-lens-lyart-nine.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.replace("Bearer ", "").strip()


@app.get("/")
def root():
    return {"message": "TruthLens backend is running"}


@app.post("/auth/register", response_model=TokenResponse)
def register_user(payload: UserRegister):
    existing_user = get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    password_hash = hash_password(payload.password)
    user_id = create_user(
        full_name=payload.full_name or "",
        email=payload.email,
        password_hash=password_hash,
    )
    user = get_user_by_id(user_id)
    token = create_access_token(user_id=user["id"], email=user["email"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"] or "",
            "email": user["email"],
            "created_at": user["created_at"],
        },
    }


@app.post("/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user_id=user["id"], email=user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"] or "",
            "email": user["email"],
            "created_at": user["created_at"],
        },
    }


@app.get("/auth/me", response_model=UserPublic)
def get_me(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token.",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return {
        "id": user["id"],
        "full_name": user["full_name"] or "",
        "email": user["email"],
        "created_at": user["created_at"],
    }


@app.get("/news", response_model=List[NewsItem])
def get_news(country: Optional[str] = None, category: Optional[str] = None):
    return get_news_from_db(country=country, category=category)


@app.get("/categories", response_model=List[str])
def get_categories():
    return get_categories_from_db()


@app.get("/trending", response_model=List[TrendingTopic])
def get_trending(region: Optional[str] = None):
    return get_trending_topics(region=region)


@app.get("/stats/overview", response_model=OverviewStats)
def stats_overview():
    return get_overview_stats()


@app.get("/refresh/logs", response_model=List[RefreshLog])
def refresh_logs():
    return get_refresh_logs()


@app.post("/news/refresh")
def refresh_news_now():
    try:
        result = run_ingestion_pipeline("manual_refresh")
        return {"status": "ok", **result}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {str(exc)}",
        ) from exc


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_content(payload: AnalyzeRequest):
    result = analyze_payload(text=payload.text, url=payload.url)

    content = payload.url or payload.text or ""
    input_type = "url" if payload.url else "text"
    save_user_check(input_type=input_type, input_value=content, result=result)

    return result


@app.post("/chat", response_model=ChatResponse)
def chat_with_assistant(payload: ChatRequest):
    service = ChatService()
    try:
        return service.chat(payload)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


if settings.enable_debug_endpoints:
    @app.get("/debug/health")
    def debug_health():
        return {
            "app_env": settings.app_env,
            "gemini_enabled": settings.gemini_enabled,
            "newsapi_enabled": settings.newsapi_enabled,
            "gnews_enabled": settings.gnews_enabled,
            "guardian_enabled": settings.guardian_enabled,
            "gdelt_enabled": settings.gdelt_enabled,
            "x_enabled": settings.x_enabled,
            "reddit_enabled": settings.reddit_enabled,
            "instagram_enabled": settings.instagram_provider_enabled,
            "tiktok_enabled": settings.tiktok_provider_enabled,
        }
