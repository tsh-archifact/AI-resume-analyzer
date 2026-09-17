# AI Resume Analyzer

FastAPI service for extracting resume and job-description text, comparing skills, generating recruiter-style analysis, and rewriting resumes with an LLM.

## Current Progress

### Completed

- FastAPI application factory and Uvicorn entrypoint.
- Health check endpoint.
- Multipart file uploads for resumes and job descriptions.
- Text extraction for PDF, DOC/DOCX, TXT, Markdown, CSV, and RTF files.
- English OCR extraction for PNG, JPG, and JPEG files with EasyOCR.
- Shared text cleanup for extracted content.
- Upload extension validation and temporary-file cleanup.
- Rule-based skill extraction as a local backup when LLM skill extraction is unavailable.
- LLM-based skill extraction using structured JSON responses.
- Case-insensitive skill comparison with matched skills, missing skills, and Jaccard-style percentage score.
- LLM recruiter analysis with structured Pydantic validation.
- Rule-based analysis when the analysis LLM is unavailable.
- LLM resume rewriting with DOCX file generation and download response.
- Clear `503` errors for resume rewriting when the API key is missing, the LLM returns no content, or the LLM request fails.
- Provider-aware configuration for Groq and OpenAI-compatible clients.
- SQLite-backed user registration and authentication with PBKDF2 password hashing.
- JWT bearer access tokens with expiration and role claims.
- Authorization protection on resume comparison and rewrite endpoints.
- Structured resume and job-description profiles with LLM extraction, spaCy validation, evidence snippets, experience inference, and weighted ATS comparison.

### Current Limitations and Follow-ups

- Automated pytest suite is established under `test/` with 29 passing unit and integration tests.
- EasyOCR initializes a reader for each image extraction, so OCR can be slow and resource-heavy. A shared reader could improve repeated requests.
- OCR currently supports English only: `easyocr.Reader(["en"])`.
- Resume rewriting intentionally has no local fallback. It returns an API error when the LLM is unavailable.
- Resume comparison and skill extraction still use local heuristic fallbacks when the LLM is unavailable.
- Structured comparison requires both the configured LLM and spaCy model; it returns HTTP `503` when either is unavailable.
- Input content is extracted and sent to the configured LLM, so deployments should consider file-size limits, privacy requirements, and sensitive resume data handling.

## API Endpoints

### `GET /health`

Returns:

```json
{"status": "ok"}
```

### Authentication

#### `POST /auth/register`

Creates a user from JSON:

```json
{
	"username": "candidate",
	"password": "a-secure-password"
}
```

Passwords must contain at least 8 characters. New users receive the `user` role.

#### `POST /auth/login`

Accepts OAuth2 form data, not JSON:

```text
username=candidate
password=a-secure-password
```

Returns an access token. In Swagger UI, use the **Authorize** button and enter the token as a bearer token.

#### `GET /auth/me`

Returns the authenticated user's ID, username, and role. Send the token in the header:

```text
Authorization: Bearer <access_token>
```

The `/compare-skill-sections`, `/compare-resume`, and `/rewrite-resume` endpoints require the same bearer token. `/health`, `/auth/register`, and `/auth/login` are public.

### `POST /compare-skill-sections`

Accepts JSON containing `resume_skills` and `job_description_skills`. Returns matched skills, missing skills, a match score, and a heuristic recommendation.

### `POST /compare-resume`

Accepts multipart fields named `resume` and either `job_description` or `job_description_text`.

The resume is required as a file and accepts only PDF, DOC, or DOCX. The job description can be uploaded as a file or provided directly as text, but not both.

Supported resume extensions:

```text
.pdf .doc .docx
```

Supported job-description file extensions:

```text
.pdf .doc .docx .txt .png .jpg .jpeg
```

The endpoint extracts both files, identifies skills, calculates similarity, and returns a `ResumeComparisonResponse` containing:

- uploaded filenames
- extracted resume skills
- extracted job-description skills
- matched and missing skills
- match score
- LLM or rule-based recruiter analysis
- structured resume and job-description profiles with keywords, skills, experience, requirements, and evidence
- required/preferred skill matches, experience fit, component scores, and a weighted overall ATS score

### `POST /rewrite-resume`

Accepts the same multipart fields and supported file types as `/compare-resume`. The endpoint extracts the resume, reads the uploaded or direct-text job description, asks the configured LLM to rewrite the resume truthfully, creates `rewritten_resume.docx`, and returns it as a download.

Rewrite failures return JSON with HTTP `503`, for example:

```json
{
	"detail": "Resume rewrite unavailable: LLM API key is not configured."
}
```

Interactive API documentation is available at `/docs` while the server is running.

## Project Structure

```text
main.py                         FastAPI app factory and Uvicorn entrypoint
api/routes.py                   Aggregator router preserving canonical API routes
api/resume_routes.py            Resume extraction, comparison, and health routes
api/agent_routes.py             Agent reflection rewrite, templates, and DOCX routes
api/auth_routes.py              Authentication and user registration routes
config/llm_setup.py             Provider, model, and API-key configuration
schemas/resume.py               Pydantic resume and JD data models
schemas/agent.py                Pydantic multi-agent audit and reflection models
services/text_extraction_service.py
                                PDF, DOCX, text, and image OCR extraction
services/markdown_converter_service.py
                                Structured markdown formatting for resumes & JDs
services/skill_service.py       LLM and heuristic skill extraction/comparison
services/analysis_service.py    Structured LLM and rule-based analysis
services/resume_rewrite_service.py
                                Orchestration for LLM and agentic resume rewriting
services/docx_generator_service.py
                                ATS-compliant DOCX resume generator with 5 templates
services/agents/                Autonomous multi-agent system (Auditor, Drafter, Fact-Checker)
services/prompts.py             Prompts for skill extraction, analysis, and rewriting
utils/file_utils.py             Upload validation, temp files, and JD resolution
utils/logger.py                 Centralized pipeline logging (logs/pipeline.log)
utils/limiter.py                SlowAPI rate limiting configuration
test/                           Automated pytest test suite (29 tests)
```

## Setup

The project uses Python 3.14 or newer and `uv` for dependency management.

```powershell
uv sync
Copy-Item .env.example .env
```

Set the provider credentials in `.env`:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=groq/compound-mini
SPACY_MODEL=en_core_web_sm
JWT_SECRET_KEY=replace_with_a_random_secret_at_least_32_characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`JWT_SECRET_KEY` is required and must contain at least 32 characters. Keep it private and use a different value in production. Users are stored in the local `auth.db` SQLite database, which is ignored by Git.

The configuration also supports OpenAI:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
```

Never commit `.env`, API keys, private resumes, or generated temporary files.

## Run the Server

Using the project environment:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Or using `uv`:

```powershell
uv run python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Validation

Compile the application modules:

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py api\routes.py services\*.py schemas\*.py utils\*.py config\*.py
```

Run tests when they are added:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Dependencies

Direct dependencies are kept in `pyproject.toml`:

- `fastapi`, `uvicorn`, and `python-multipart`: API server and uploads.
- `groq`: Groq LLM client.
- `httpx`: HTTP client support and API testing compatibility.
- `pypdf2`: PDF text extraction.
- `python-docx`: DOCX reading and rewritten DOCX generation.
- `easyocr` and `pillow`: PNG/JPG/JPEG OCR support.
- `spacy`: NLP tokenization and validation for structured profile extraction.
- `python-dotenv`: `.env` configuration loading.
Packages such as PyTorch, TorchVision, SciPy, OpenCV, NumPy, and Shapely are transitive EasyOCR dependencies. They should not be removed while image OCR is enabled.

## Development History

1. Started with PDF, DOCX, and plain-text extraction plus text cleanup.
2. Added FastAPI routes and multipart uploads.
3. Added structured Pydantic schemas for skill comparison and recommendations.
4. Added Groq/provider configuration and LLM skill extraction.
5. Added heuristic fallbacks for skill extraction, similarity, and comparison analysis.
6. Added resume rewriting and DOCX downloads.
7. Added PNG/JPEG support with EasyOCR after Mineru installation failed on Windows because of a native C++ build dependency.
8. Refactored behavior into `api`, `services`, `schemas`, `config`, and `utils` modules.
9. Removed the resume rewrite fallback so unavailable LLM requests now produce clear `503` API errors.
