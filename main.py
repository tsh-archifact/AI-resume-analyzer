from fastapi import FastAPI

from api.auth_routes import router as auth_router
from api.routes import router
from services.auth_service import init_auth_database


def create_app() -> FastAPI:
    app = FastAPI(title="AI Resume Analyzer API")
    init_auth_database()
    app.include_router(auth_router)
    app.include_router(router)
    return app


app = create_app()


def main():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
