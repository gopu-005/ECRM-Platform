"""
Generic repository base class with tenant isolation support.
All repositories must pass organization_id in every query.
"""
from __future__ import annotations
from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository with multi-tenant row-level isolation.
    All public methods require organization_id to ensure tenant safety.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession):
        self.model = model
        self.session = session

    def _base_query(self, organization_id: str):
        """Build a base query filtered by organization_id and not soft-deleted."""
        stmt = select(self.model).where(
            self.model.organization_id == organization_id
        )
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return stmt

    async def get_by_id(
        self, id: str, organization_id: str, options: list = None
    ) -> Optional[ModelT]:
        stmt = self._base_query(organization_id).where(self.model.id == id)
        if options:
            stmt = stmt.options(*options)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        organization_id: str,
        filters: list[Any] = None,
        order_by: Any = None,
        skip: int = 0,
        limit: int = 20,
        options: list = None,
    ) -> tuple[List[ModelT], int]:
        """Returns (items, total_count)."""
        stmt = self._base_query(organization_id)
        if filters:
            stmt = stmt.where(and_(*filters))

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Data
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        if options:
            stmt = stmt.options(*options)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, data: dict) -> ModelT:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, data: dict) -> ModelT:
        for key, value in data.items():
            if value is not None or key in data:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> ModelT:
        from datetime import datetime, timezone
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return obj

    async def hard_delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def count(self, organization_id: str, filters: list = None) -> int:
        stmt = self._base_query(organization_id)
        if filters:
            stmt = stmt.where(and_(*filters))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return (await self.session.execute(count_stmt)).scalar() or 0
