"""Bid plan service — AI-generated task plan management."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.bid_plan import BidPlan, BidPlanTask

logger = logging.getLogger(__name__)


class BidPlanService:
    """Service for bid plan CRUD and task management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_project(self, project_id: UUID) -> BidPlan:
        """Get the bid plan for a project."""
        result = await self.db.execute(
            select(BidPlan).where(BidPlan.project_id == project_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("BidPlan", str(project_id))
        return plan

    async def create_or_update(
        self,
        project_id: UUID,
        title: str = "",
        deadline: datetime | None = None,
    ) -> BidPlan:
        """Create or update a bid plan for a project."""
        result = await self.db.execute(
            select(BidPlan).where(BidPlan.project_id == project_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            if title:
                plan.title = title
            if deadline:
                plan.submission_deadline = deadline
            plan.updated_at = datetime.now(UTC)
        else:
            plan = BidPlan(
                project_id=project_id,
                title=title or "Bid Preparation Plan",
                submission_deadline=deadline,
            )
            self.db.add(plan)

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def list_tasks(self, plan_id: UUID) -> list[BidPlanTask]:
        """List all tasks in a bid plan."""
        result = await self.db.execute(
            select(BidPlanTask)
            .where(BidPlanTask.plan_id == plan_id)
            .order_by(BidPlanTask.order_index)
        )
        return list(result.scalars().all())

    async def add_task(
        self,
        plan_id: UUID,
        title: str,
        description: str = "",
        assignee: str = "",
        due_date: datetime | None = None,
        order_index: int = 0,
    ) -> BidPlanTask:
        """Add a task to a bid plan."""
        task = BidPlanTask(
            plan_id=plan_id,
            title=title,
            description=description,
            assignee=assignee,
            due_date=due_date,
            order_index=order_index,
            status="pending",
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task_status(
        self,
        task_id: UUID,
        status: str,
    ) -> BidPlanTask:
        """Update a task's status."""
        result = await self.db.execute(
            select(BidPlanTask).where(BidPlanTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("BidPlanTask", str(task_id))

        task.status = status
        task.updated_at = datetime.now(UTC)
        if status == "completed":
            task.completed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: UUID) -> None:
        """Delete a task from a bid plan."""
        result = await self.db.execute(
            select(BidPlanTask).where(BidPlanTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("BidPlanTask", str(task_id))

        await self.db.delete(task)
        await self.db.commit()
