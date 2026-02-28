"""Stats service — operational, user, and financial statistics."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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

        return {
            "total_users": user_count or 0,
            "total_projects": project_count or 0,
            "total_opportunities": opp_count or 0,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_daily_stats(
        self,
        days: int = 30,
    ) -> list[dict]:
        """Get daily statistics for the past N days."""
        since = datetime.now(UTC) - timedelta(days=days)

        result = await self.db.execute(
            select(DailyStats)
            .where(DailyStats.date >= since.date())
            .order_by(DailyStats.date.desc())
        )
        rows = result.scalars().all()

        return [
            {
                "date": str(row.date),
                "new_users": row.new_users,
                "active_users": row.active_users,
                "new_projects": row.new_projects,
                "api_calls": row.api_calls,
                "credits_consumed": row.credits_consumed,
            }
            for row in rows
        ]

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get statistics for a specific user."""
        project_count = await self.db.scalar(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )

        credits_used = await self.db.scalar(
            select(func.sum(func.abs(PaymentTransaction.amount)))
            .where(
                PaymentTransaction.user_id == user_id,
                PaymentTransaction.transaction_type == "deduction",
            )
        )

        return {
            "projects": project_count or 0,
            "credits_consumed": int(credits_used or 0),
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
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            credits_consumed=credits_consumed,
            metadata=metadata or {},
        )
        self.db.add(log)
        await self.db.commit()
