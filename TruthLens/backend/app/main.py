from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalyzeRequest,
    ChatRequest,
    ChatResponse,
    NewsItem,
    UserRegister,
    UserLogin,
    UserPublic,
    TokenResponse,
)
from app.analyzer import analyze_text_content
from app.chat_service import ChatService
from app.database import (
    init_db,
    seed_news_if_empty,
    get_news_from_db,
    get_categories_from_db,
    save_user_check,
    get_connection,
    create_user,
    get_user_by_email,
    get_user_by_id,
)
from app.auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_news_if_empty()
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="TruthLens API",
    description="Backend API for real-time credibility analysis and news monitoring.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://192.168.56.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization.replace("Bearer ", "").strip()


@app.get("/")
def root():
    return {"message": "TruthLens backend is running with SQLite"}


@app.post("/auth/register", response_model=TokenResponse)
def register_user(payload: UserRegister):
    existing_user = get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    password_hash = hash_password(payload.password)
    user_id = create_user(
        full_name=payload.full_name or "",
        email=payload.email,
        password_hash=password_hash
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
        }
    }


@app.post("/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin):
    user = get_user_by_email(payload.email)

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
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
        }
    }


@app.get("/auth/me", response_model=UserPublic)
def get_me(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token."
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

    user_id = int(payload["sub"])
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
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


@app.post("/analyze")
def analyze_content(payload: AnalyzeRequest):
    content = payload.text or payload.url or ""
    result = analyze_text_content(content)

    input_type = "url" if payload.url else "text"
    save_user_check(input_type=input_type, input_value=content, result=result)

    return result


@app.post("/chat", response_model=ChatResponse)
def chat_with_assistant(payload: ChatRequest):
    service = ChatService()
    return service.chat(payload)


@app.get("/debug/news-count")
def debug_news_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM news_articles")
    count = cursor.fetchone()["count"]
    conn.close()
    return {"news_count": count}


@app.get("/debug/user-checks")
def debug_user_checks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, input_type, input_value, credibility_score,
               credibility_label, explanation, created_at
        FROM user_checks
        ORDER BY id DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/debug/users")
def debug_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, email, created_at
        FROM users
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
