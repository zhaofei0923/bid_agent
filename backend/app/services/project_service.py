"""Project service — CRUD and status management."""

import math
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.project import Project
from app.schemas.project import (
    PaginatedProjects,
    ProjectCreate,
    ProjectUpdate,
)


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: UUID, data: ProjectCreate) -> Project:
        project = Project(
            name=data.name,
            description=data.description,
            opportunity_id=data.opportunity_id,
            institution=data.institution,
            user_id=user_id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: UUID, user_id: UUID) -> Project:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))
        if project.user_id != user_id:
            raise AuthorizationError("You do not own this project")
        return project

    async def list_by_user(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> PaginatedProjects:
        stmt = select(Project).where(Project.user_id == user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Project.updated_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return PaginatedProjects(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    async def update(
        self, project_id: UUID, user_id: UUID, data: ProjectUpdate
    ) -> Project:
        project = await self.get_by_id(project_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: UUID, user_id: UUID) -> None:
        """Delete a project via raw SQL to avoid ORM session conflicts
        caused by lazy='selectin' pre-loading related objects.
        DB ON DELETE CASCADE handles child rows automatically.
        """
        # Verify ownership first
        project = await self.get_by_id(project_id, user_id)
        # Expunge from session before raw SQL to avoid stale-state conflicts
        self.db.expunge(project)
        await self.db.execute(
            sql_delete(Project).where(Project.id == project_id)
        )
        await self.db.commit()
