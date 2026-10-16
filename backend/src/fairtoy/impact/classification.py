from __future__ import annotations

from .contracts import (
    AFFECTED,
    PART_ALL_SOURCES_FLAGGED_REASON_CODE,
    PART_MIXED_SOURCE_FLAGS_REASON_CODE,
    PART_NO_FLAGGED_SOURCES_REASON_CODE,
    PART_NO_KNOWN_SOURCES_REASON_CODE,
    POTENTIALLY_AFFECTED,
    TOY_AFFECTED_REASON_CODE,
    TOY_POTENTIALLY_AFFECTED_REASON_CODE,
    TOY_UNAFFECTED_REASON_CODE,
    UNAFFECTED,
    ImpactPath,
    ImpactReasonCode,
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
    status, reason_code, reason = _part_status(paths)
    return PartImpact(
        part_id=part_id,
        part_name=part_name,
        quantity=quantity,
        status=status,
        reason_code=reason_code,
        reason=reason,
        paths=paths,
    )


def classify_toy(
    parts: tuple[PartImpact, ...],
) -> tuple[ImpactStatus, ImpactReasonCode, str]:
    statuses = {part.status for part in parts}
    if AFFECTED in statuses:
        return (
            AFFECTED,
            TOY_AFFECTED_REASON_CODE,
            "At least one required part is affected.",
        )
    if POTENTIALLY_AFFECTED in statuses:
        return (
            POTENTIALLY_AFFECTED,
            TOY_POTENTIALLY_AFFECTED_REASON_CODE,
            "At least one required part is potentially affected.",
        )
    return (
        UNAFFECTED,
        TOY_UNAFFECTED_REASON_CODE,
        "No required part is affected or potentially affected.",
    )


def _part_status(
    paths: tuple[ImpactPath, ...],
) -> tuple[ImpactStatus, ImpactReasonCode, str]:
    if not paths:
        return (
            UNAFFECTED,
            PART_NO_KNOWN_SOURCES_REASON_CODE,
            "No known possible sources exist for this part.",
        )

    flagged_count = sum(path.supplier_flagged for path in paths)
    if flagged_count == 0:
        return (
            UNAFFECTED,
            PART_NO_FLAGGED_SOURCES_REASON_CODE,
            "No possible sources for this part are flagged.",
        )
    if flagged_count == len(paths):
        return (
            AFFECTED,
            PART_ALL_SOURCES_FLAGGED_REASON_CODE,
            "All known possible sources for this part are flagged.",
        )
    return (
        POTENTIALLY_AFFECTED,
        PART_MIXED_SOURCE_FLAGS_REASON_CODE,
        "This part has both flagged and unflagged possible sources.",
    )
