from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from fairtoy.impact import (
    AFFECTED,
    POTENTIALLY_AFFECTED,
    UNAFFECTED,
    ImpactInputError,
    TraceabilityFact,
    calculate_impact,
)


def source_fact(
    *,
    part_id: str = "PRT-1",
    quantity: int = 2,
    supplier_id: str = "SUP-1",
    factory_id: str = "FAC-1",
    flagged: bool = False,
) -> TraceabilityFact:
    return TraceabilityFact(
        toy_id="TOY-1",
        toy_name="Test Toy",
        part_id=part_id,
        part_name=f"Part {part_id}",
        quantity=quantity,
        supplier_id=supplier_id,
        supplier_name=f"Supplier {supplier_id}",
        supplier_flagged=flagged,
        factory_id=factory_id,
        factory_name=f"Factory {factory_id}",
        unit_cost_usd=Decimal("1.00"),
    )


def no_source_fact(
    *,
    part_id: str = "PRT-1",
    quantity: int = 2,
) -> TraceabilityFact:
    return TraceabilityFact(
        toy_id="TOY-1",
        toy_name="Test Toy",
        part_id=part_id,
        part_name=f"Part {part_id}",
        quantity=quantity,
    )


def test_unflagged_source_is_unaffected_and_explainable() -> None:
    result = calculate_impact([source_fact()])

    assert result[0].status == UNAFFECTED
    assert result[0].parts[0].status == UNAFFECTED
    assert result[0].parts[0].quantity == 2
    assert len(result[0].parts[0].paths) == 1
    assert result[0].parts[0].paths[0].supplier_flagged is False


def test_part_with_no_known_sources_is_unaffected() -> None:
    result = calculate_impact([no_source_fact()])

    assert result[0].status == UNAFFECTED
    assert result[0].parts[0].status == UNAFFECTED
    assert result[0].parts[0].paths == ()
    assert "No known possible sources" in result[0].parts[0].reason


def test_mixed_sources_are_potentially_affected() -> None:
    result = calculate_impact(
        [
            source_fact(
                supplier_id="SUP-2",
                factory_id="FAC-2",
                flagged=False,
            ),
            source_fact(
                supplier_id="SUP-1",
                factory_id="FAC-1",
                flagged=True,
            ),
        ]
    )

    part = result[0].parts[0]
    assert result[0].status == POTENTIALLY_AFFECTED
    assert part.status == POTENTIALLY_AFFECTED
    assert [path.factory_id for path in part.paths] == ["FAC-1", "FAC-2"]


def test_all_known_sources_are_affected() -> None:
    result = calculate_impact(
        [
            source_fact(
                supplier_id="SUP-1",
                factory_id="FAC-1",
                flagged=True,
            ),
            source_fact(
                supplier_id="SUP-2",
                factory_id="FAC-2",
                flagged=True,
            ),
        ]
    )

    assert result[0].status == AFFECTED
    assert result[0].parts[0].status == AFFECTED


def test_affected_toy_status_takes_precedence_over_potential() -> None:
    result = calculate_impact(
        [
            source_fact(
                part_id="PRT-A",
                supplier_id="SUP-1",
                factory_id="FAC-1",
                flagged=True,
            ),
            source_fact(
                part_id="PRT-A",
                supplier_id="SUP-2",
                factory_id="FAC-2",
                flagged=False,
            ),
            source_fact(
                part_id="PRT-B",
                supplier_id="SUP-3",
                factory_id="FAC-3",
                flagged=True,
            ),
        ]
    )

    assert result[0].status == AFFECTED
    assert [part.part_id for part in result[0].parts] == ["PRT-A", "PRT-B"]
    assert result[0].parts[0].status == POTENTIALLY_AFFECTED
    assert result[0].parts[1].status == AFFECTED


def test_unflagging_changes_the_next_calculation() -> None:
    flagged_fact = source_fact(flagged=True)

    assert calculate_impact([flagged_fact])[0].status == AFFECTED
    assert (
        calculate_impact([replace(flagged_fact, supplier_flagged=False)])[0].status
        == UNAFFECTED
    )


def test_duplicate_facts_are_deduplicated_and_results_are_sorted() -> None:
    part_b = source_fact(
        part_id="PRT-B",
        supplier_id="SUP-2",
        factory_id="FAC-2",
    )
    part_a = source_fact(
        part_id="PRT-A",
        supplier_id="SUP-1",
        factory_id="FAC-1",
    )

    result = calculate_impact([part_b, part_a, part_b])

    assert [part.part_id for part in result[0].parts] == ["PRT-A", "PRT-B"]
    assert len(result[0].parts[1].paths) == 1


def test_conflicting_supplier_flags_are_rejected() -> None:
    with pytest.raises(ImpactInputError, match="conflicting flags"):
        calculate_impact(
            [
                source_fact(
                    part_id="PRT-A",
                    supplier_id="SUP-1",
                    factory_id="FAC-1",
                    flagged=True,
                ),
                source_fact(
                    part_id="PRT-B",
                    supplier_id="SUP-1",
                    factory_id="FAC-2",
                    flagged=False,
                ),
            ]
        )


def test_source_and_no_source_facts_cannot_be_mixed() -> None:
    with pytest.raises(ImpactInputError, match="mixes source"):
        calculate_impact(
            [
                no_source_fact(),
                source_fact(),
            ]
        )
