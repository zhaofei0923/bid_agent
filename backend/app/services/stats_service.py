"""Stats service — operational, user, and financial statistics."""

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_analysis import BidAnalysis
from app.models.opportunity import Opportunity
from app.models.payment import PaymentTransaction
from app.models.project import Project
from app.models.stats import DailyStats, UsageLog
from app.models.user import User

logger = logging.getLogger(__name__)


class StatsService:
    """Service for statistics aggregation (admin-only)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_overview(self) -> dict:
        """Get overall system statistics."""
        user_count = await self.db.scalar(select(func.count(User.id)))
        project_count = await self.db.scalar(select(func.count(Project.id)))
        opp_count = await self.db.scalar(select(func.count(Opportunity.id)))
        analysis_count = await self.db.scalar(select(func.count(BidAnalysis.id)))
        today = datetime.now(UTC).date()
        active_users_today = await self.db.scalar(
            select(func.count(func.distinct(UsageLog.user_id))).where(
                func.date(UsageLog.created_at) == today
            )
        )

        return {
            "total_users": user_count or 0,
            "total_projects": project_count or 0,
            "total_opportunities": opp_count or 0,
            "total_analyses": analysis_count or 0,
            "active_users_today": active_users_today or 0,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_daily_stats(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get daily statistics for a date range."""
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        result = await self.db.execute(
            select(DailyStats)
            .where(
                DailyStats.stat_date >= start_date,
                DailyStats.stat_date <= end_date,
            )
            .order_by(DailyStats.stat_date.asc())
        )
        rows = result.scalars().all()

        by_date: dict[date, dict] = {}
        for row in rows:
            bucket = by_date.setdefault(
                row.stat_date,
                {
                    "date": row.stat_date.isoformat(),
                    "new_users": 0,
                    "active_users": 0,
                    "new_projects": 0,
                    "api_calls": 0,
                    "credits_consumed": 0,
                },
            )
            if row.metric_type in bucket:
                bucket[row.metric_type] = int(row.metric_value or row.metric_count or 0)

        return [by_date[key] for key in sorted(by_date)]

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get statistics for a specific user."""
        project_count = await self.db.scalar(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )
        analyses_count = await self.db.scalar(
            select(func.count(BidAnalysis.id))
            .join(Project, Project.id == BidAnalysis.project_id)
            .where(Project.user_id == user_id)
        )

        credits_used = await self.db.scalar(
            select(func.sum(func.abs(PaymentTransaction.amount)))
            .where(
                PaymentTransaction.user_id == user_id,
                PaymentTransaction.amount < 0,
            )
        )
        last_active = await self.db.scalar(
            select(func.max(UsageLog.created_at)).where(UsageLog.user_id == user_id)
        )

        return {
            "projects_count": project_count or 0,
            "analyses_count": analyses_count or 0,
            "credits_consumed": int(credits_used or 0),
            "last_active": last_active.isoformat() if last_active else None,
        }

    async def log_usage(
        self,
        user_id: UUID,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        credits_consumed: int = 0,
        metadata: dict | None = None,
    ) -> None:
        """Log a usage event."""
        log = UsageLog(
            user_id=user_id,
            action_type=action,
            resource_type=resource_type,
            resource_id=UUID(resource_id) if resource_id else None,
            credits_consumed=credits_consumed,
            metadata_=metadata or {},
        )
        self.db.add(log)
        await self.db.commit()
