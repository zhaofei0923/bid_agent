"""Bid plan API routes — plan CRUD and task management."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.bid_plan_service import BidPlanService
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/{project_id}/plan")
async def get_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the bid plan for a project."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    return await plan_svc.get_by_project(project_id)


@router.post("/{project_id}/plan")
async def create_or_update_plan(
    project_id: UUID,
    title: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    return await plan_svc.create_or_update(project_id, title=title)


@router.get("/{project_id}/plan/tasks")
async def list_tasks(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks in a bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    plan = await plan_svc.get_by_project(project_id)
    return await plan_svc.list_tasks(plan.id)


@router.post("/{project_id}/plan/tasks")
async def add_task(
    project_id: UUID,
    title: str,
    description: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a task to the bid plan."""
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    plan_svc = BidPlanService(db)
    plan = await plan_svc.get_by_project(project_id)
    return await plan_svc.add_task(plan.id, title=title, description=description)


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
    return await plan_svc.update_task_status(task_id, status)


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
    await plan_svc.delete_task(task_id)
    return {"message": "Task deleted"}
