"""Skill base classes and context objects."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import LLMClient


@dataclass
class SkillContext:
    """Execution context passed to every Skill."""

    project_id: UUID
    db: AsyncSession
    llm_client: LLMClient
    parameters: dict = field(default_factory=dict)


@dataclass
class SkillResult:
    """Standardised output from a Skill execution."""

    success: bool
    data: dict = field(default_factory=dict)
    tokens_consumed: int = 0
    sources: list[dict] = field(default_factory=list)
    error: str | None = None


class Skill(ABC):
    """Abstract base class for all Skills.

    A Skill is an atomic analysis unit that combines:
    - Vector retrieval from bid docs and/or knowledge base
    - LLM call to interpret / structure the retrieved content
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, ctx: SkillContext) -> SkillResult:
        """Run the skill and return structured results."""
        ...
