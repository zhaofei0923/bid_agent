"""Bid plan service — AI-generated task plan management."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import LLMClient
from app.agents.skills.base import SkillContext
from app.agents.skills.generate_plan import (
    GeneratePlan,
    _build_analysis_summary,
    _extract_deadline,
)
from app.core.exceptions import NotFoundError
from app.models.bid_analysis import BidAnalysis
from app.models.bid_plan import BidPlan, BidPlanTask
from app.models.project import Project

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
        result = await self.db.execute(
            select(BidPlan).where(BidPlan.project_id == project_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            if title:
                plan.name = title
            plan.updated_at = datetime.now(UTC)
        else:
            plan = BidPlan(
                project_id=project_id,
                name=title or "Bid Preparation Plan",
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
            .order_by(BidPlanTask.sort_order)
        )
        return list(result.scalars().all())

    async def add_task(
        self,
        plan_id: UUID,
        title: str,
        description: str = "",
        assignee: str = "",
        due_date: datetime | None = None,
        sort_order: int = 0,
    ) -> BidPlanTask:
        """Add a task to a bid plan."""
        task = BidPlanTask(
            plan_id=plan_id,
            title=title,
            description=description,
            assignee=assignee,
            due_date=due_date,
            sort_order=sort_order,
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

    async def generate_ai_plan(
        self,
        project_id: UUID,
        llm_client: LLMClient,
    ) -> tuple[BidPlan, list[BidPlanTask]]:
        """Generate an AI-powered task plan from existing bid analysis results.

        Returns (plan, tasks).  Deletes previous AI-generated tasks before
        inserting the freshly generated ones; manually added tasks are kept.
        """
        # Fetch project to get institution
        proj_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))

        # Fetch analysis results
        analysis_result = await self.db.execute(
            select(BidAnalysis).where(BidAnalysis.project_id == project_id)
        )
        analysis = analysis_result.scalar_one_or_none()

        analysis_summary = _build_analysis_summary(analysis) if analysis else ""
        deadline = _extract_deadline(analysis.key_dates if analysis else None) or "未知"
        institution = project.institution or "adb"

        # Call GeneratePlan Skill
        ctx = SkillContext(
            project_id=project_id,
            db=self.db,
            llm_client=llm_client,
            parameters={
                "analysis_summary": analysis_summary,
                "deadline": deadline,
                "institution": institution,
            },
        )
        skill = GeneratePlan()
        skill_result = await skill.execute(ctx)

        if not skill_result.success:
            raise RuntimeError(f"Plan generation failed: {skill_result.error}")

        generated_tasks: list[dict] = skill_result.data.get("tasks", [])
        plan_summary: str = skill_result.data.get("plan_summary", "")

        # Upsert BidPlan
        plan_db_result = await self.db.execute(
            select(BidPlan).where(BidPlan.project_id == project_id)
        )
        plan = plan_db_result.scalar_one_or_none()
        if plan:
            plan.description = plan_summary or plan.description
            plan.generated_by_ai = True
            plan.model_used = llm_client.model
            plan.updated_at = datetime.now(UTC)
        else:
            plan = BidPlan(
                project_id=project_id,
                name="投标准备计划",
                description=plan_summary,
                generated_by_ai=True,
                model_used=llm_client.model,
            )
            self.db.add(plan)
            await self.db.flush()  # get plan.id

        # Delete previous AI-generated tasks (keep manual ones)
        await self.db.execute(
            delete(BidPlanTask).where(
                BidPlanTask.plan_id == plan.id,
            )
        )

        # Bulk-insert new tasks
        new_tasks: list[BidPlanTask] = []
        for i, task_data in enumerate(generated_tasks):
            due_date_raw = task_data.get("due_date")
            due_date = None
            if due_date_raw and due_date_raw != "null":
                try:
                    from datetime import date
                    due_date = date.fromisoformat(str(due_date_raw))
                except (ValueError, TypeError):
                    due_date = None

            task = BidPlanTask(
                plan_id=plan.id,
                title=task_data.get("title", f"任务 {i + 1}"),
                description=task_data.get("description", ""),
                category=task_data.get("category", "administrative"),
                priority=task_data.get("priority", "medium"),
                sort_order=task_data.get("sort_order", i + 1),
                status="pending",
                due_date=due_date,
            )
            self.db.add(task)
            new_tasks.append(task)

        # Update task count
        plan.total_tasks = len(new_tasks)
        plan.completed_tasks = 0

        await self.db.commit()
        await self.db.refresh(plan)
        for task in new_tasks:
            await self.db.refresh(task)

        logger.info(
            "AI plan generated for project %s: %d tasks", project_id, len(new_tasks)
        )
        return plan, new_tasks
