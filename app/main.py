from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="mxy-python API",
        version="0.1.0",
        description="FastAPI + LangChain 1.x starter project",
    )

    # CORS settings for frontend / other services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount versioned API router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
