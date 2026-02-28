"""Stats and analytics API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform overview stats (admin only)."""
    service = StatsService(db)
    return await service.get_overview()


@router.get("/daily")
async def get_daily_stats(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get daily stats in a date range (admin only)."""
    service = StatsService(db)
    return await service.get_daily_stats(start_date, end_date)


@router.get("/users/me")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's usage stats."""
    service = StatsService(db)
    return await service.get_user_stats(current_user.id)
