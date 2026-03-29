"""API v1 router registry."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bid_analysis import router as bid_analysis_router
from app.api.v1.bid_documents import router as bid_documents_router
from app.api.v1.bid_plan import router as bid_plan_router
from app.api.v1.document_review import router as document_review_router
from app.api.v1.guidance import router as guidance_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.payment import router as payment_router
from app.api.v1.projects import router as projects_router
from app.api.v1.public import router as public_router
from app.api.v1.quality_review import router as quality_review_router
from app.api.v1.reading_tips import router as reading_tips_router
from app.api.v1.stats import router as stats_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(
    public_router, prefix="/public", tags=["public"]
)
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(
    opportunities_router, prefix="/opportunities", tags=["opportunities"]
)
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(
    bid_documents_router, prefix="/projects", tags=["bid-documents"]
)
api_router.include_router(
    bid_analysis_router, prefix="/projects", tags=["bid-analysis"]
)
api_router.include_router(
    guidance_router, prefix="/projects", tags=["guidance"]
)
api_router.include_router(
    knowledge_base_router, prefix="/knowledge-bases", tags=["knowledge-base"]
)
api_router.include_router(
    bid_plan_router, prefix="/projects", tags=["bid-plan"]
)
api_router.include_router(
    quality_review_router, prefix="/projects", tags=["quality-review"]
)
api_router.include_router(
    document_review_router, prefix="/projects", tags=["document-review"]
)
api_router.include_router(
    reading_tips_router, prefix="/projects", tags=["reading-tips"]
)
api_router.include_router(
    payment_router, prefix="/payment", tags=["payment"]
)
api_router.include_router(
    stats_router, prefix="/stats", tags=["stats"]
)
api_router.include_router(
    admin_router, prefix="/admin", tags=["admin"]
)
