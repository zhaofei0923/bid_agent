"""Bid plan service — AI-generated task plan management."""

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import LLMClient
from app.agents.skills.base import SkillContext
from app.agents.skills.generate_plan import (
    GeneratePlan,
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
        description: str | None = None,
        deadline: datetime | None = None,
    ) -> BidPlan:
        result = await self.db.execute(
            select(BidPlan).where(BidPlan.project_id == project_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            if title:
                plan.name = title
            if description is not None:
                plan.description = description
            plan.updated_at = datetime.now(UTC)
        else:
            plan = BidPlan(
                project_id=project_id,
                name=title or "Bid Preparation Plan",
                description=description,
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
        category: str | None = None,
        priority: str = "medium",
        assignee: str = "",
        start_date: date | None = None,
        due_date: date | None = None,
        sort_order: int = 0,
        status: str = "pending",
        notes: str | None = None,
        related_document: str | None = None,
        reference_page: int | None = None,
    ) -> BidPlanTask:
        """Add a task to a bid plan."""
        task = BidPlanTask(
            plan_id=plan_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            assignee=assignee,
            start_date=start_date,
            due_date=due_date,
            sort_order=sort_order,
            status=status,
            notes=notes,
            related_document=related_document,
            reference_page=reference_page,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task_status(
        self,
        task_id: UUID,
        status: str,
        plan_id: UUID,
    ) -> BidPlanTask:
        """Update a task's status."""
        result = await self.db.execute(
            select(BidPlanTask).where(
                BidPlanTask.id == task_id,
                BidPlanTask.plan_id == plan_id,
            )
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

    async def delete_task(self, task_id: UUID, plan_id: UUID) -> None:
        """Delete a task from a bid plan."""
        result = await self.db.execute(
            select(BidPlanTask).where(
                BidPlanTask.id == task_id,
                BidPlanTask.plan_id == plan_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("BidPlanTask", str(task_id))

        await self.db.delete(task)
        await self.db.commit()

    async def update_task(
        self,
        task_id: UUID,
        plan_id: UUID,
        **fields: object,
    ) -> BidPlanTask:
        """Update arbitrary fields on a task."""
        result = await self.db.execute(
            select(BidPlanTask).where(
                BidPlanTask.id == task_id,
                BidPlanTask.plan_id == plan_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("BidPlanTask", str(task_id))

        allowed = {
            "title", "description", "category", "priority",
            "start_date", "due_date", "assignee", "notes", "sort_order", "status",
            "related_document", "reference_page",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(task, key, value)

        task.updated_at = datetime.now(UTC)
        if fields.get("status") == "completed":
            task.completed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def reorder_tasks(self, plan_id: UUID, task_ids: list[UUID]) -> None:
        """Reorder tasks by the given ID sequence."""
        for idx, tid in enumerate(task_ids):
            await self.db.execute(
                update(BidPlanTask)
                .where(BidPlanTask.id == tid, BidPlanTask.plan_id == plan_id)
                .values(sort_order=idx + 1, updated_at=datetime.now(UTC))
            )
        await self.db.commit()

    async def generate_ai_plan(
        self,
        project_id: UUID,
        llm_client: LLMClient,
    ) -> tuple[BidPlan, list[BidPlanTask]]:
        """Generate an AI-powered task plan from existing bid analysis results.

        Returns (plan, tasks).  Deletes all previous tasks before
        inserting the freshly generated ones.
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

        deadline = _extract_deadline(analysis.key_dates if analysis else None) or "未知"
        institution = project.institution or "adb"

        # Build structured context from analysis dimensions
        params: dict = {
            "deadline": deadline,
            "institution": institution,
            "key_dates": getattr(analysis, "key_dates", None),
            "qualification_requirements": getattr(analysis, "qualification_requirements", None),
            "evaluation_criteria": getattr(analysis, "evaluation_criteria", None),
            "submission_checklist": getattr(analysis, "submission_checklist", None),
            "commercial_terms": getattr(analysis, "commercial_terms", None),
            "risk_assessment": getattr(analysis, "risk_assessment", None),
        }

        # Call GeneratePlan Skill
        ctx = SkillContext(
            project_id=project_id,
            db=self.db,
            llm_client=llm_client,
            parameters=params,
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

            start_date_raw = task_data.get("start_date")
            start_date = None
            if start_date_raw and start_date_raw != "null":
                try:
                    from datetime import date as _date_cls
                    start_date = _date_cls.fromisoformat(str(start_date_raw))
                except (ValueError, TypeError):
                    start_date = None

            task = BidPlanTask(
                plan_id=plan.id,
                title=task_data.get("title", f"任务 {i + 1}"),
                description=task_data.get("description", ""),
                category=task_data.get("category", "documents"),
                priority=task_data.get("priority", "medium"),
                sort_order=task_data.get("sort_order", i + 1),
                status="pending",
                start_date=start_date,
                due_date=due_date,
                related_document=task_data.get("related_document"),
                reference_page=task_data.get("reference_page"),
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
