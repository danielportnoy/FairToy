from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .classification import classify_part, classify_toy
from .contracts import (
    ImpactInputError,
    ImpactPath,
    PartImpact,
    ToyTraceability,
    ToyImpact,
    TraceabilityFact,
    TOY_UNAFFECTED_REASON_CODE,
    UNAFFECTED,
)
from .validation import (
    ConsistencyRegistry,
    FactIdentity,
    source_path_from_fact,
    validate_fact,
)


@dataclass
class _PartGroup:
    part_name: str
    quantity: int
    paths_by_factory: dict[str, ImpactPath]
    has_no_source_fact: bool = False


def calculate_impact(
    facts: Iterable[TraceabilityFact],
) -> tuple[ToyImpact, ...]:
    """Classify canonical Toys from current Supplier flag facts.

    The result is global at the Toy level. FinisherToy filtering belongs to a
    repository or API layer and does not change this calculation.
    """

    registry = ConsistencyRegistry()
    grouped: dict[str, dict[str, _PartGroup]] = {}

    for fact in facts:
        identity = validate_fact(fact)
        path = source_path_from_fact(fact)
        registry.validate(identity, path)
        _add_fact(grouped, identity, fact.quantity, path)

    return _build_results(grouped, registry)


def calculate_toy_impact(toy: ToyTraceability) -> ToyImpact:
    """Classify one Finisher-scoped Toy while preserving empty Toys."""

    if not toy.facts:
        return ToyImpact(
            toy_id=toy.toy_id,
            toy_name=toy.toy_name,
            status=UNAFFECTED,
            reason_code=TOY_UNAFFECTED_REASON_CODE,
            reason="No required part is affected or potentially affected.",
            parts=(),
        )

    results = calculate_impact(toy.facts)
    if len(results) != 1:
        raise ImpactInputError(
            f"facts for toy {toy.toy_id!r} produced {len(results)} Toys"
        )
    result = results[0]
    if result.toy_id != toy.toy_id or result.toy_name != toy.toy_name:
        raise ImpactInputError(
            f"facts do not match ToyTraceability {toy.toy_id!r}"
        )
    return result


def calculate_toy_impacts(
    toys: Iterable[ToyTraceability],
) -> tuple[ToyImpact, ...]:
    """Classify a deterministic sequence of Finisher-scoped Toys."""

    return tuple(calculate_toy_impact(toy) for toy in toys)


def _add_fact(
    grouped: dict[str, dict[str, _PartGroup]],
    identity: FactIdentity,
    quantity: int,
    path: ImpactPath | None,
) -> None:
    parts_for_toy = grouped.setdefault(identity.toy_id, {})
    part_group = parts_for_toy.get(identity.part_id)
    if part_group is None:
        part_group = _PartGroup(
            part_name=identity.part_name,
            quantity=quantity,
            paths_by_factory={},
        )
        parts_for_toy[identity.part_id] = part_group
    else:
        _validate_existing_part(part_group, identity, quantity)

    if path is None:
        _add_no_source_fact(part_group, identity)
        return
    _add_source_fact(part_group, identity, path)


def _validate_existing_part(
    part_group: _PartGroup,
    identity: FactIdentity,
    quantity: int,
) -> None:
    if part_group.part_name != identity.part_name:
        raise ImpactInputError(
            f"part_id {identity.part_id!r} has conflicting names"
        )
    if part_group.quantity != quantity:
        raise ImpactInputError(
            f"ToyPart {(identity.toy_id, identity.part_id)!r} "
            "has conflicting quantities"
        )


def _add_no_source_fact(
    part_group: _PartGroup,
    identity: FactIdentity,
) -> None:
    if part_group.paths_by_factory:
        raise ImpactInputError(
            f"ToyPart {(identity.toy_id, identity.part_id)!r} mixes source "
            "and no-source facts"
        )
    part_group.has_no_source_fact = True


def _add_source_fact(
    part_group: _PartGroup,
    identity: FactIdentity,
    path: ImpactPath,
) -> None:
    if part_group.has_no_source_fact:
        raise ImpactInputError(
            f"ToyPart {(identity.toy_id, identity.part_id)!r} mixes source "
            "and no-source facts"
        )
    existing_path = part_group.paths_by_factory.get(path.factory_id)
    if existing_path is not None and existing_path != path:
        raise ImpactInputError(
            f"source {(identity.part_id, path.factory_id)!r} "
            "has conflicting facts"
        )
    part_group.paths_by_factory[path.factory_id] = path


def _build_results(
    grouped: dict[str, dict[str, _PartGroup]],
    registry: ConsistencyRegistry,
) -> tuple[ToyImpact, ...]:
    results = []
    for toy_id in sorted(grouped):
        parts = tuple(
            _build_part_impact(part_id, grouped[toy_id][part_id])
            for part_id in sorted(grouped[toy_id])
        )
        toy_status, toy_reason_code, toy_reason = classify_toy(parts=parts)
        results.append(
            ToyImpact(
                toy_id=toy_id,
                toy_name=registry.toy_names[toy_id],
                status=toy_status,
                reason_code=toy_reason_code,
                reason=toy_reason,
                parts=parts,
            )
        )
    return tuple(results)


def _build_part_impact(
    part_id: str,
    part_group: _PartGroup,
) -> PartImpact:
    paths = tuple(
        sorted(
            part_group.paths_by_factory.values(),
            key=lambda path: (path.factory_id, path.supplier_id),
        )
    )
    return classify_part(
        part_id=part_id,
        part_name=part_group.part_name,
        quantity=part_group.quantity,
        paths=paths,
    )
