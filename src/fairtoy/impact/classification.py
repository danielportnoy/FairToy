from __future__ import annotations

from .contracts import (
    AFFECTED,
    POTENTIALLY_AFFECTED,
    UNAFFECTED,
    ImpactPath,
    ImpactStatus,
    PartImpact,
)


def classify_part(
    *,
    part_id: str,
    part_name: str,
    quantity: int,
    paths: tuple[ImpactPath, ...],
) -> PartImpact:
    status, reason = _part_status(paths)
    return PartImpact(
        part_id=part_id,
        part_name=part_name,
        quantity=quantity,
        status=status,
        reason=reason,
        paths=paths,
    )


def classify_toy(
    parts: tuple[PartImpact, ...],
) -> tuple[ImpactStatus, str]:
    statuses = {part.status for part in parts}
    if AFFECTED in statuses:
        return AFFECTED, "At least one required part is affected."
    if POTENTIALLY_AFFECTED in statuses:
        return (
            POTENTIALLY_AFFECTED,
            "At least one required part is potentially affected.",
        )
    return (
        UNAFFECTED,
        "No required part is affected or potentially affected.",
    )


def _part_status(
    paths: tuple[ImpactPath, ...],
) -> tuple[ImpactStatus, str]:
    if not paths:
        return (
            UNAFFECTED,
            "No known possible sources exist for this part.",
        )

    flagged_count = sum(path.supplier_flagged for path in paths)
    if flagged_count == 0:
        return (
            UNAFFECTED,
            "No possible sources for this part are flagged.",
        )
    if flagged_count == len(paths):
        return (
            AFFECTED,
            "All known possible sources for this part are flagged.",
        )
    return (
        POTENTIALLY_AFFECTED,
        "This part has both flagged and unflagged possible sources.",
    )
