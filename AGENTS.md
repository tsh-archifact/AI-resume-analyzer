# Repository Guidelines

## Project Structure & Module Organization

This is a FastAPI service for resume analysis and rewriting.

### Backend (FastAPI)

- `main.py`: application entry point and FastAPI app factory.
- `api/`: modular HTTP endpoints (`routes.py`, `resume_routes.py`, `agent_routes.py`, `auth_routes.py`).
- `schemas/`: Pydantic request and response models (`resume.py`, `agent.py`, `auth.py`).
- `services/`: business logic, including multi-agent reflection loops (`agents/`), LLM prompts, skill extraction, text extraction, analysis, markdown conversion, and resume rewriting.
- `utils/`: file upload validation, temporary file handling, job description resolution, and logging.
- `config/`: environment-driven LLM provider/model/client setup.
- `test/`: automated pytest test suite (`test_*.py`).

### Frontend (React + Vite + TypeScript)

- `frontend/`: single-page React application built with Vite and TypeScript.
  - `src/main.tsx`: application entry point.
  - `src/App.tsx`: root component with routing setup.
  - `src/pages/`: page-level components.
  - `src/components/`: reusable UI components.
  - `src/api/`: API client functions for communicating with the FastAPI backend.
  - `src/context/`: React context providers for shared state.
  - `src/types/`: TypeScript type definitions.
  - `src/assets/`: static assets (images, icons, etc.).

## Build, Test, and Development Commands

Use the project virtual environment when available:

### Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Runs the API locally at `http://127.0.0.1:8000`.

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py api\routes.py services\*.py schemas\*.py utils\*.py config\*.py
```

Checks Python syntax/import compatibility.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Runs tests once a pytest suite is added.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Runs the frontend dev server at `http://localhost:5173`.

```powershell
npm run build
```

Builds the frontend for production into `frontend/dist/`.

```powershell
npm run lint
```

Lints the frontend code with oxlint.

## Coding Style & Naming Conventions

Use Python 3.14 syntax, 4-space indentation, and type hints for public functions. Keep route handlers thin; place business logic in `services/`. Use clear module names ending in `_service.py` for service-layer code. Pydantic models should live in `schemas/` and use PascalCase class names, for example `ResumeComparisonResponse`.

Keep comments short and purposeful. Prefer docstrings for public helpers when they explain intent, not obvious mechanics.

## Testing Guidelines

Place tests under `test/` and name files `test_<feature>.py`. Focus tests on service functions first, such as skill extraction, similarity calculation, text formatting, and fallback behavior. For API tests, use FastAPI’s test client and small sample text files rather than real private resumes.

## Commit & Pull Request Guidelines

This repository has no existing commit history yet. Use concise, imperative commit messages, for example:

```text
Refactor resume rewrite service
Add upload validation tests
```

Pull requests should include a short summary, verification steps, and notes about any LLM/provider behavior changes. Do not include `.env`, API keys, private resumes, or generated temporary files.

## Security & Configuration Tips

Copy `.env.example` to `.env` and set provider credentials locally. Keep `.env` out of git. If Groq returns `model_not_found`, update `LLM_MODEL` to a model available to your account, such as `groq/compound-mini`.
