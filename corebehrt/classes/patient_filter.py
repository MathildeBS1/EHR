from typing import Optional

import pandas as pd

from corebehrt.common.constants import (
    PID_COL,
    TIMESTAMP_COL,
    BIRTHDATE_COL,
    DEATHDATE_COL,
)


def filter_by_categories(
    patients_info: pd.DataFrame, category_filters: Optional[dict] = None
) -> pd.DataFrame:
    """Filter patients by categorical variables.

    Args:
        patients_info: DataFrame with category columns
        category_filters: Dict of {column: {'include': [...]} or {'exclude': [...]}}
    """
    if not category_filters:
        return patients_info

    for col, rule in category_filters.items():
        include = rule.get("include")
        exclude = rule.get("exclude")

        if include:
            patients_info = patients_info[patients_info[col].isin(include)]
        elif exclude:
            patients_info = patients_info[~patients_info[col].isin(exclude)]

    return patients_info


def filter_by_age(
    patients_info: pd.DataFrame,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
) -> pd.DataFrame:
    """Filter patients by age range at their index date.

    Args:
        patients_info: DataFrame with BIRTHDATE_COL and TIMESTAMP_COL (index date) columns in datetime format
        min_age: Minimum age in years (inclusive)
        max_age: Maximum age in years (inclusive)
    """
    age_in_years = (
        patients_info[TIMESTAMP_COL] - patients_info[BIRTHDATE_COL]
    ).dt.total_seconds() / (365.25 * 24 * 60 * 60)
    if min_age is not None:
        patients_info = patients_info[age_in_years >= min_age]

    if max_age is not None:
        patients_info = patients_info[age_in_years <= max_age]

    return patients_info


def apply_exclusion_filters(
    patients_info: pd.DataFrame,
    outcomes: pd.DataFrame,
    outcome_before_index_date: bool = False,
) -> pd.DataFrame:
    """Remove patients based on death and outcome criteria.

    Args:
        patients_info: DataFrame with DEATHDATE_COL and TIMESTAMP_COL columns in datetime format
        index_dates: Series of reference dates for exclusion in datetime format
        outcomes: DataFrame with PID and TIMESTAMP columns in datetime format
        dead_before_index_date: Exclude patients who died before index date
        outcome_before_index_date: Exclude patients with prior outcomes
    """
    patients_info = patients_info[
        patients_info[DEATHDATE_COL].isna()
        | (patients_info[DEATHDATE_COL] > patients_info[TIMESTAMP_COL])
    ]

    if outcome_before_index_date and not outcomes.empty:
        earliest_outcomes = outcomes.groupby(PID_COL)[TIMESTAMP_COL].min()

        # Align earliest_outcomes with the patients we still have
        earliest_outcomes = earliest_outcomes.reindex(patients_info[PID_COL].unique())

        # Ensure patients_info is indexed by PID to compare properly
        indexed_patients_info = patients_info.set_index(PID_COL, drop=False)

        # Determine which patients to exclude:
        pids_to_exclude = indexed_patients_info.index[
            (earliest_outcomes < indexed_patients_info[TIMESTAMP_COL])
        ]

        # Filter them out
        patients_info = patients_info[~patients_info[PID_COL].isin(pids_to_exclude)]

    return patients_info


def filter_df_by_pids(df: pd.DataFrame, pids: list) -> pd.DataFrame:
    """Filter using PID column in dataframe."""
    return df[df[PID_COL].isin(pids)]
