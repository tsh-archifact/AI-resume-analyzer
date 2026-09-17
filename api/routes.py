"""
Unified API Router.
Combines domain-specific routers (resume comparison and agentic rewriting)
to provide a single router for application mount while preserving modularity.
"""

from fastapi import APIRouter

from api.agent_routes import router as agent_router
from api.resume_routes import router as resume_router

router = APIRouter()
router.include_router(resume_router)
router.include_router(agent_router)

__all__ = ["router", "resume_router", "agent_router"]
