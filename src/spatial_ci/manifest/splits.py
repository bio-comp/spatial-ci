import hashlib

import polars as pl


def _stable_fraction(split_contract_id: str, resolved_patient_id: str) -> float:
    payload = f"{split_contract_id}:{resolved_patient_id}".encode()
    digest = hashlib.sha256(payload).digest()
    bucket = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return bucket / 2**64


def assign_patient_splits(
    frame: pl.DataFrame,
    *,
    split_contract_id: str,
    val_fraction: float,
    external_holdout_cohorts: list[str],
) -> pl.DataFrame:
    """Assign one deterministic split per resolved patient and join to samples."""

    if not 0.0 < val_fraction < 1.0:
        raise ValueError("val_fraction must be strictly between 0 and 1")

    holdout_cohorts = set(external_holdout_cohorts)
    patient_rows = frame.select(["cohort_id", "resolved_patient_id"]).unique()

    assignments: list[dict[str, str]] = []
    for row in patient_rows.to_dicts():
        cohort_id = str(row["cohort_id"])
        resolved_patient_id = str(row["resolved_patient_id"])
        if cohort_id in holdout_cohorts:
            split = "holdout"
        else:
            fraction = _stable_fraction(split_contract_id, resolved_patient_id)
            split = (
                "val"
                if fraction < val_fraction
                else "train"
            )
        assignments.append(
            {
                "cohort_id": cohort_id,
                "resolved_patient_id": resolved_patient_id,
                "split": split,
            }
        )

    assignment_frame = pl.DataFrame(assignments)
    return frame.join(
        assignment_frame,
        on=["cohort_id", "resolved_patient_id"],
        how="left",
        validate="m:1",
    )
