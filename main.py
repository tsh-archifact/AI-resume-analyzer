import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth_routes import router as auth_router
from api.routes import router
from services.auth_service import init_auth_database

# adding the dependencies of the slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from utils.limiter import limiter
from slowapi.errors import RateLimitExceeded
def create_app() -> FastAPI:
    app = FastAPI(title="AI Resume Analyzer API")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    init_auth_database()

    cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth_router)
    app.include_router(router)
    return app


app = create_app()


def main():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
