from fastapi import FastAPI

from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Resume Analyzer API")
    app.include_router(router)
    return app


app = create_app()


def main():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
