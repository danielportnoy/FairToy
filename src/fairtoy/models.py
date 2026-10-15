from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Finisher(Base):
    __tablename__ = "finishers"

    finisher_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finisher_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hq_country: Mapped[str | None] = mapped_column(String(128), nullable=True)

    finisher_toys: Mapped[list["FinisherToy"]] = relationship(
        back_populates="finisher",
        passive_deletes=True,
    )


class Toy(Base):
    __tablename__ = "toys"

    toy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    toy_name: Mapped[str] = mapped_column(String(255), nullable=False)

    finisher_toys: Mapped[list["FinisherToy"]] = relationship(
        back_populates="toy",
        passive_deletes=True,
    )
    toy_parts: Mapped[list["ToyPart"]] = relationship(
        back_populates="toy",
        passive_deletes=True,
    )


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hq_country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    child_labor_flagged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    flagged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    factories: Mapped[list["Factory"]] = relationship(
        back_populates="supplier",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "(child_labor_flagged = 0 AND flagged_at IS NULL) "
            "OR (child_labor_flagged = 1 AND flagged_at IS NOT NULL)",
            name="ck_suppliers_flagged_at_consistent",
        ),
    )


class Factory(Base):
    __tablename__ = "factories"

    factory_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("suppliers.supplier_id", ondelete="RESTRICT"),
        nullable=False,
    )
    factory_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)

    supplier: Mapped[Supplier] = relationship(back_populates="factories")
    part_sources: Mapped[list["PartSource"]] = relationship(
        back_populates="factory",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_factories_supplier_id", "supplier_id"),
    )


class Part(Base):
    __tablename__ = "parts"

    part_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)

    toy_parts: Mapped[list["ToyPart"]] = relationship(
        back_populates="part",
        passive_deletes=True,
    )
    part_sources: Mapped[list["PartSource"]] = relationship(
        back_populates="part",
        passive_deletes=True,
    )


class FinisherToy(Base):
    __tablename__ = "finisher_toys"

    finisher_id: Mapped[str] = mapped_column(
        ForeignKey("finishers.finisher_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    toy_id: Mapped[str] = mapped_column(
        ForeignKey("toys.toy_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    retail_price_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    units_per_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    finisher: Mapped[Finisher] = relationship(back_populates="finisher_toys")
    toy: Mapped[Toy] = relationship(back_populates="finisher_toys")

    __table_args__ = (
        Index("ix_finisher_toys_toy_id", "toy_id"),
        CheckConstraint(
            "retail_price_usd IS NULL OR retail_price_usd >= 0",
            name="ck_finisher_toys_retail_price_non_negative",
        ),
        CheckConstraint(
            "units_per_year IS NULL OR units_per_year >= 0",
            name="ck_finisher_toys_units_non_negative",
        ),
    )


class ToyPart(Base):
    __tablename__ = "toy_parts"

    toy_id: Mapped[str] = mapped_column(
        ForeignKey("toys.toy_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    part_id: Mapped[str] = mapped_column(
        ForeignKey("parts.part_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    toy: Mapped[Toy] = relationship(back_populates="toy_parts")
    part: Mapped[Part] = relationship(back_populates="toy_parts")

    __table_args__ = (
        Index("ix_toy_parts_part_id", "part_id"),
        CheckConstraint(
            "quantity >= 0",
            name="ck_toy_parts_quantity_non_negative",
        ),
    )


class PartSource(Base):
    __tablename__ = "part_sources"

    part_id: Mapped[str] = mapped_column(
        ForeignKey("parts.part_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    factory_id: Mapped[str] = mapped_column(
        ForeignKey("factories.factory_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    unit_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    part: Mapped[Part] = relationship(back_populates="part_sources")
    factory: Mapped[Factory] = relationship(back_populates="part_sources")

    __table_args__ = (
        Index("ix_part_sources_factory_id", "factory_id"),
        CheckConstraint(
            "unit_cost_usd IS NULL OR unit_cost_usd >= 0",
            name="ck_part_sources_unit_cost_non_negative",
        ),
    )
