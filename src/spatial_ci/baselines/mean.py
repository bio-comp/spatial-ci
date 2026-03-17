"""Mean-based deployable baseline predictors."""

import polars as pl

from spatial_ci.baselines.artifacts import BaselineName

REQUIRED_COLUMNS = {
    "observation_id",
    "sample_id",
    "cohort_id",
    "split",
    "program_name",
    "raw_rank_evidence",
}


def _validate_required_columns(frame: pl.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"baseline input frame is missing columns: {missing_display}")


def _eligible_rows(frame: pl.DataFrame) -> pl.DataFrame:
    _validate_required_columns(frame)
    eligible = frame
    if "status" in frame.columns:
        eligible = eligible.filter(pl.col("status") == "ok")

    if eligible.height == 0:
        raise ValueError("baseline input frame has no eligible score rows")
    return eligible.select(
        [
            "observation_id",
            "sample_id",
            "cohort_id",
            "split",
            "program_name",
            "raw_rank_evidence",
        ]
    )


def _train_means_by_program(frame: pl.DataFrame) -> pl.DataFrame:
    train = frame.filter(pl.col("split") == "train")
    if train.height == 0:
        raise ValueError("baseline input frame has no train rows")
    return train.group_by("program_name").agg(
        pl.col("raw_rank_evidence").mean().alias("predicted_score")
    )


def predict_global_train_mean(frame: pl.DataFrame) -> pl.DataFrame:
    """Predict each program with the train-only global mean."""

    eligible = _eligible_rows(frame)
    program_means = _train_means_by_program(eligible)
    predictions = eligible.join(program_means, on="program_name", how="left")
    if predictions.get_column("predicted_score").null_count() > 0:
        raise ValueError("missing global train mean for one or more programs")
    return predictions.select(
        [
            "observation_id",
            "sample_id",
            "cohort_id",
            "split",
            "program_name",
            pl.lit(BaselineName.GLOBAL_TRAIN_MEAN.value).alias("baseline_name"),
            "predicted_score",
        ]
    )


def predict_mean_by_train_cohort(frame: pl.DataFrame) -> pl.DataFrame:
    """Predict each program with matching train-cohort mean, else global mean."""

    eligible = _eligible_rows(frame)
    train = eligible.filter(pl.col("split") == "train")
    if train.height == 0:
        raise ValueError("baseline input frame has no train rows")

    cohort_means = train.group_by(["program_name", "cohort_id"]).agg(
        pl.col("raw_rank_evidence").mean().alias("cohort_predicted_score")
    )
    global_means = _train_means_by_program(eligible).rename(
        {"predicted_score": "global_predicted_score"}
    )
    predictions = (
        eligible.join(cohort_means, on=["program_name", "cohort_id"], how="left")
        .join(global_means, on="program_name", how="left")
        .with_columns(
            pl.coalesce(
                ["cohort_predicted_score", "global_predicted_score"]
            ).alias("predicted_score")
        )
    )
    if predictions.get_column("predicted_score").null_count() > 0:
        raise ValueError("missing mean_by_train_cohort prediction for one or more rows")
    return predictions.select(
        [
            "observation_id",
            "sample_id",
            "cohort_id",
            "split",
            "program_name",
            pl.lit(BaselineName.MEAN_BY_TRAIN_COHORT.value).alias("baseline_name"),
            "predicted_score",
        ]
    )


__all__ = [
    "predict_global_train_mean",
    "predict_mean_by_train_cohort",
]
