# AI Resume Analyzer — Frontend

React + TypeScript frontend built with Vite for the FastAPI resume analyzer backend.

## Features

- User registration and sign-in against `/auth/*` endpoints
- Resume vs. job-description comparison with skill tags, match score, and LLM analysis
- Resume rewrite download as DOCX
- Drag-and-drop file uploads and pasted job-description text
- Vite dev-server proxy to the backend at `http://127.0.0.1:8000`

## Setup

From the repository root:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
```

## Run

Start the backend first:

```powershell
cd ..
uv run python -m uvicorn main:app --reload
```

Then start the frontend:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Build

```powershell
npm run build
npm run preview
```

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | API base path. Use the Vite proxy in development or set a full backend URL in production. |

The backend must allow the frontend origin. `main.py` defaults to:

```text
http://127.0.0.1:5173,http://localhost:5173
```

Override with `CORS_ORIGINS` in the backend `.env` if needed.
