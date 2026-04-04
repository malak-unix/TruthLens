# TruthLens

TruthLens is a web app for monitoring viral news, assigning an explainable credibility score, and helping users verify content before sharing it.

## Live Demo

- Production app: `https://truth-lens-lyart-nine.vercel.app/`

## Stack

- Frontend: Next.js 16 + React 19
- Backend: FastAPI
- Database: SQLite
- Auth: JWT
- Scheduler: APScheduler

## Current MVP Features

- Dashboard with Morocco / World filtering
- Category filtering and search
- Fact-Check Corner connected to `POST /analyze`
- Assistant panel connected to `POST /chat`
- SQLite-backed news feed
- User signup, login, and current-user session lookup
- Internal scheduler for morning / midday / evening news refresh

## Project Structure

```text
TruthLens/
|-- backend/
|   |-- app/
|   |-- requirements.txt
|   `-- truthlens.db
`-- frontend/
    |-- app/
    |-- components/
    |-- lib/
    `-- package.json
```

## Prerequisites

- Python 3.13+
- Node.js 20+
- npm

## Backend Setup

Open a PowerShell terminal in `TruthLens/backend`.

If `.venv` does not exist yet:

```powershell
py -3.13 -m venv .venv
```

Install backend dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the FastAPI server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Available backend URLs:

- API root: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Frontend Setup

Open a second PowerShell terminal in `TruthLens/frontend`.

Create the local env file from the example:

```powershell
Copy-Item .env.example .env.local
```

Install frontend dependencies:

```powershell
npm install
```

Run the frontend:

```powershell
npm run dev
```

Frontend URL:

- App: `http://localhost:3000`

## Minimal Launch Flow

1. Start the backend on port `8000`.
2. Start the frontend on port `3000`.
3. Open `http://localhost:3000`.
4. Test the dashboard news loading.
5. Test the Fact-Check Corner.
6. Test the Assistant panel.
7. Test signup, login, and profile reload.

## Main Backend Routes

- `GET /`
- `GET /news`
- `GET /categories`
- `POST /analyze`
- `POST /chat`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /debug/news-count`
- `GET /debug/user-checks`
- `GET /debug/users`

## Notes

- The backend initializes SQLite automatically through the FastAPI lifespan.
- The scheduler starts automatically with the backend and registers morning, midday, and evening refresh jobs.
- `truthlens.db` is tracked in Git for MVP/demo purposes, so avoid committing test users or fake test checks.
- The credibility score is heuristic and explainable; it is not a claim of absolute truth.

## Quick Verification

After startup, these checks should pass:

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/categories
```

Then confirm in the browser:

- dashboard loads articles
- region/category filters react correctly
- analysis returns score, label, and explanation
- assistant returns a scoped response with suggested checks
- signup/login flow works
