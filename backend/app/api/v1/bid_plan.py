"""Bid plan API routes — plan CRUD and task management."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.core.exceptions import ConflictError
from app.core.security import get_current_user
from app.database import get_db
from app.models.bid_plan import BidPlan
from app.models.user import User
from app.services.bid_plan_service import BidPlanService
from app.services.project_service import ProjectService

router = APIRouter()


def _orm_to_dict(obj: object) -> dict:
    """Convert a SQLAlchemy ORM object to a plain dict (columns only, no relationships)."""
    data = {
        c.key: getattr(obj, c.key)
        for c in sa_inspect(type(obj)).mapper.column_attrs
    }
    if "assignee" in data:
        data["assigned_to"] = data["assignee"]
    return data


# ── Pydantic schemas for request bodies ──────────────────────────

class TaskUpdateBody(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    assignee: str | None = None
    assigned_to: str | None = None
    notes: str | None = None
    sort_order: int | None = None
    status: str | None = None
    related_document: str | None = None
    reference_page: int | None = None


class ReorderBody(BaseModel):
    task_ids: list[str]


class PlanUpsertBody(BaseModel):
    title: str | None = None
    name: str | None = None
    description: str | None = None


class TaskCreateBody(TaskUpdateBody):
    title: str


# ── Plan routes ──────────────────────────────────────────────────

@router.get("/{project_id}/plan")
async def get_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the bid plan for a project. Returns null if no plan exists yet."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    try:
        plan = await plan_svc.get_by_project(project_id)
        return _orm_to_dict(plan)
    except Exception:
        return None


@router.post("/{project_id}/plan")
async def create_or_update_plan(
    project_id: UUID,
    body: PlanUpsertBody | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    title = body.title or body.name if body else ""
    description = body.description if body else None
    plan = await plan_svc.create_or_update(
        project_id, title=title or "", description=description
    )
    return _orm_to_dict(plan)


# ── Task routes ──────────────────────────────────────────────────

@router.get("/{project_id}/plan/tasks")
async def list_tasks(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks in a bid plan. Returns [] if no plan exists yet."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    try:
        plan = await plan_svc.get_by_project(project_id)
    except Exception:
        return []
    tasks = await plan_svc.list_tasks(plan.id)
    return [_orm_to_dict(t) for t in tasks]


@router.post("/{project_id}/plan/tasks")
async def add_task(
    project_id: UUID,
    body: TaskCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a task to the bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    try:
        plan = await plan_svc.get_by_project(project_id)
    except Exception:
        plan = await plan_svc.create_or_update(project_id)
    fields = body.model_dump(exclude_none=True)
    if "assigned_to" in fields:
        fields["assignee"] = fields.pop("assigned_to")
    task = await plan_svc.add_task(plan.id, **fields)
    return _orm_to_dict(task)


@router.patch("/{project_id}/plan/tasks/{task_id}")
async def update_task(
    project_id: UUID,
    task_id: UUID,
    body: TaskUpdateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task fields (title, description, category, priority, due_date, etc.)."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    fields = body.model_dump(exclude_none=True)
    if "assigned_to" in fields:
        fields["assignee"] = fields.pop("assigned_to")
    plan = await plan_svc.get_by_project(project_id)
    task = await plan_svc.update_task(task_id, plan.id, **fields)
    return _orm_to_dict(task)


@router.put("/{project_id}/plan/tasks/{task_id}/status")
async def update_task_status(
    project_id: UUID,
    task_id: UUID,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task's status."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    plan = await plan_svc.get_by_project(project_id)
    task = await plan_svc.update_task_status(task_id, status, plan.id)
    return _orm_to_dict(task)


@router.delete("/{project_id}/plan/tasks/{task_id}")
async def delete_task(
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task from the bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    plan = await plan_svc.get_by_project(project_id)
    await plan_svc.delete_task(task_id, plan.id)
    return {"message": "Task deleted"}


@router.post("/{project_id}/plan/reorder")
async def reorder_tasks(
    project_id: UUID,
    body: ReorderBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder tasks by the given ID sequence."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    plan = await plan_svc.get_by_project(project_id)
    await plan_svc.reorder_tasks(plan.id, [UUID(tid) for tid in body.task_ids])
    return {"message": "Tasks reordered"}


# ── AI generation (one-time only) ────────────────────────────────

@router.post("/{project_id}/plan/generate")
async def generate_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI bid preparation task plan (one-time only)."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    # Prevent duplicate generation
    result = await db.execute(
        select(BidPlan).where(
            BidPlan.project_id == project_id,
            BidPlan.generated_by_ai.is_(True),
        )
    )
    if result.scalar_one_or_none():
        raise ConflictError("投标计划已通过 AI 生成，不可重复生成。")

    llm_client = get_llm_client()
    plan_svc = BidPlanService(db)
    plan, tasks = await plan_svc.generate_ai_plan(project_id, llm_client)
    return {
        "plan": _orm_to_dict(plan),
        "tasks": [_orm_to_dict(t) for t in tasks],
    }
