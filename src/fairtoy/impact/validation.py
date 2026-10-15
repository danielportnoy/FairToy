from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .contracts import (
    ImpactInputError,
    ImpactPath,
    TraceabilityFact,
)


@dataclass(frozen=True)
class FactIdentity:
    toy_id: str
    toy_name: str
    part_id: str
    part_name: str


@dataclass
class ConsistencyRegistry:
    toy_names: dict[str, str] = field(default_factory=dict)
    part_names: dict[str, str] = field(default_factory=dict)
    supplier_names: dict[str, str] = field(default_factory=dict)
    supplier_flags: dict[str, bool] = field(default_factory=dict)
    factory_names: dict[str, str] = field(default_factory=dict)
    factory_suppliers: dict[str, str] = field(default_factory=dict)

    def validate(
        self,
        identity: FactIdentity,
        path: ImpactPath | None,
    ) -> None:
        self._validate_name(
            self.toy_names,
            identity.toy_id,
            identity.toy_name,
            "toy_id",
        )
        self._validate_name(
            self.part_names,
            identity.part_id,
            identity.part_name,
            "part_id",
        )
        if path is None:
            return

        self._validate_name(
            self.supplier_names,
            path.supplier_id,
            path.supplier_name,
            "supplier_id",
        )
        self._validate_flag(path)
        self._validate_name(
            self.factory_names,
            path.factory_id,
            path.factory_name,
            "factory_id",
        )
        previous_supplier = self.factory_suppliers.setdefault(
            path.factory_id,
            path.supplier_id,
        )
        if previous_supplier != path.supplier_id:
            raise ImpactInputError(
                f"factory_id {path.factory_id!r} has conflicting suppliers"
            )

    @staticmethod
    def _validate_name(
        names: dict[str, str],
        identity: str,
        name: str,
        field_name: str,
    ) -> None:
        previous_name = names.setdefault(identity, name)
        if previous_name != name:
            raise ImpactInputError(
                f"{field_name} {identity!r} has conflicting names"
            )

    def _validate_flag(self, path: ImpactPath) -> None:
        previous_flag = self.supplier_flags.setdefault(
            path.supplier_id,
            path.supplier_flagged,
        )
        if previous_flag != path.supplier_flagged:
            raise ImpactInputError(
                f"supplier_id {path.supplier_id!r} has conflicting flags"
            )


def _require_text(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ImpactInputError(f"{field_name} is required")
    return value


def _validate_quantity(quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ImpactInputError("quantity must be a non-negative integer")
    if quantity < 0:
        raise ImpactInputError("quantity must be a non-negative integer")


def _validate_unit_cost(unit_cost_usd: Decimal | None) -> None:
    if unit_cost_usd is None:
        return
    if not isinstance(unit_cost_usd, Decimal):
        raise ImpactInputError("unit_cost_usd must be a Decimal or None")
    if not unit_cost_usd.is_finite() or unit_cost_usd < 0:
        raise ImpactInputError(
            "unit_cost_usd must be a finite, non-negative number"
        )


def validate_fact(fact: TraceabilityFact) -> FactIdentity:
    """Validate and return the canonical identity carried by a fact."""

    identity = FactIdentity(
        toy_id=_require_text(fact.toy_id, "toy_id"),
        toy_name=_require_text(fact.toy_name, "toy_name"),
        part_id=_require_text(fact.part_id, "part_id"),
        part_name=_require_text(fact.part_name, "part_name"),
    )
    _validate_quantity(fact.quantity)
    return identity


def source_path_from_fact(
    fact: TraceabilityFact,
) -> ImpactPath | None:
    """Validate optional source columns and build an explainable path."""

    required_source_fields = (
        fact.supplier_id,
        fact.supplier_name,
        fact.supplier_flagged,
        fact.factory_id,
        fact.factory_name,
    )
    if all(value is None for value in required_source_fields):
        if fact.unit_cost_usd is not None:
            raise ImpactInputError(
                "unit_cost_usd cannot be provided without a possible source"
            )
        return None
    if any(value is None for value in required_source_fields):
        raise ImpactInputError(
            "supplier and factory source fields must be complete"
        )
    if not isinstance(fact.supplier_flagged, bool):
        raise ImpactInputError("supplier_flagged must be a boolean")

    supplier_id = _require_text(fact.supplier_id, "supplier_id")
    supplier_name = _require_text(fact.supplier_name, "supplier_name")
    factory_id = _require_text(fact.factory_id, "factory_id")
    factory_name = _require_text(fact.factory_name, "factory_name")
    _validate_unit_cost(fact.unit_cost_usd)

    return ImpactPath(
        toy_id=fact.toy_id,
        toy_name=fact.toy_name,
        part_id=fact.part_id,
        part_name=fact.part_name,
        quantity=fact.quantity,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        supplier_flagged=fact.supplier_flagged,
        factory_id=factory_id,
        factory_name=factory_name,
        unit_cost_usd=fact.unit_cost_usd,
    )
