import pandas as pd
from oda_data import ODAData

from scripts.common import EU27, LOWER_TARGET, LOWER_TARGET_COUNTRIES, TARGET
from scripts.config import Paths
from scripts.tools import (
    to_constant,
    get_gdp_growth_factor,
    extend_deflators_to_year,
    add_member_state_names,
)

MAX_DATA_YEAR = 2023


def get_total_oda_and_gni(
    years: int | list[int] = 2023, currency: str = "EUR"
) -> pd.DataFrame:

    oda = ODAData(years=years, donors=EU27 + [20918, 918], currency=currency)

    oda.load_indicator(["total_oda_official_definition", "gni"])

    df = (
        oda.get_data()
        .pivot(index=["year", "donor_code"], columns="indicator", values="value")
        .reset_index()
    )

    return df


def calculate_oda_gni_ratio(df: pd.DataFrame) -> pd.DataFrame:

    df["oda_gni_ratio"] = df["total_oda_official_definition"] / df["gni"]

    return df


def add_target_column(df: pd.DataFrame) -> pd.DataFrame:
    df["target"] = df.donor_code.map(
        lambda x: LOWER_TARGET if x in LOWER_TARGET_COUNTRIES else TARGET
    )

    return df


def _get_gni_targets_from_target_year(
    oda_df: pd.DataFrame, target_year: int, projections_end_year: int
):
    # latest data
    latest = oda_df.loc[oda_df.year == MAX_DATA_YEAR].copy()

    at_target = latest.loc[lambda d: d.oda_gni_ratio >= d.target]
    below_target = latest.loc[lambda d: d.oda_gni_ratio < d.target]

    dfs = []

    dfs.append(at_target.assign(year=target_year))
    dfs.append(below_target.assign(year=target_year, oda_gni_ratio=lambda d: d.target))

    df = pd.concat([oda_df, *dfs], ignore_index=True).filter(
        ["year", "donor_code", "oda_gni_ratio"]
    )

    return df


def _interpolate_gni_projections(
    df: pd.DataFrame,
    start_year: int,
    projections_end_year: int,
):
    # for every donor, linearly interpolate any oda_gni_ratio that is missing
    years = pd.DataFrame({"year": range(start_year, projections_end_year + 1)})

    interpolated_data = []

    for donor in df.donor_code.unique():
        donor_data = df.loc[lambda d: d.donor_code == donor].copy()
        donor_data = donor_data.merge(years, on="year", how="right").fillna(
            {"donor_code": donor}
        )
        donor_data = donor_data.sort_values("year").interpolate(method="linear")

        donor_data = donor_data.astype({"donor_code": "Int32"})

        interpolated_data.append(donor_data)

    return pd.concat(interpolated_data, ignore_index=True)


def individual_gni_targets(
    start_year: int = 2018,
    target_year: int = 2030,
    projections_end_year: int = 2034,
):
    years = list(range(start_year, MAX_DATA_YEAR + 1))
    # Get spending data
    oda_df = get_total_oda_and_gni(years=years, currency="EUR").loc[
        lambda d: d.donor_code != 918
    ]

    # Add ODA/GNI
    oda_df = calculate_oda_gni_ratio(oda_df)

    # Add targets
    oda_df = add_target_column(oda_df)

    # Get GNI targets
    df = _get_gni_targets_from_target_year(
        oda_df, target_year=target_year, projections_end_year=projections_end_year
    )

    return _interpolate_gni_projections(df, start_year, projections_end_year)


def individual_spending(
    start_year: int = 2018,
    currency: str = "EUR",
) -> pd.DataFrame:
    # Data years
    years = list(range(start_year, MAX_DATA_YEAR + 1))

    # Get spending data
    oda_df = get_total_oda_and_gni(years=years, currency=currency).loc[
        lambda d: d.donor_code != 918
    ]

    # Add ODA/GNI
    oda_df = calculate_oda_gni_ratio(oda_df)

    return oda_df


def get_gni_projections(
    oda_df: pd.DataFrame | None = None,
    last_year: int = 2034,
    prices: str = "current",
    base_year: int | None = None,
    rolling_window: int = 3,
) -> pd.DataFrame:

    if oda_df is None:
        oda_df = (
            get_total_oda_and_gni([2023])
            .filter(["year", "donor_code", "gni"])
            .dropna(subset=["gni"])
        )

    deflators = get_gdp_growth_factor(from_year=oda_df.year.max())

    deflators = deflators.pipe(
        extend_deflators_to_year, last_year, rolling_window=rolling_window
    ).loc[lambda d: d.year > oda_df.year.max()]

    gni_projection = oda_df.drop(columns="year").merge(
        deflators, left_on="donor_code", right_on="dac_code", how="right"
    )

    gni_projection["gni"] = gni_projection["gni"].astype(float)
    gni_projection["value"] = gni_projection["value"].astype(float)

    gni_projection["gni"] = gni_projection["gni"] * gni_projection["value"]

    return gni_projection.filter(["year", "donor_code", "gni"])


def eu_spending_projections(
    start_year: int = 2014, end_year: int = 2034, base_year: int = 2025
) -> pd.DataFrame:
    """"""

    targets = individual_gni_targets(
        start_year=start_year, projections_end_year=end_year
    ).assign(indicator=f"GNI targets")

    historical_constant = individual_spending(
        start_year=start_year, currency="EUR"
    ).pipe(to_constant, base_year=base_year)

    constant_projections = get_gni_projections(
        oda_df=historical_constant.loc[lambda d: d.year == d.year.max()]
        .filter(["year", "donor_code", "gni"])
        .dropna(subset=["gni"]),
        last_year=end_year,
        prices="constant",
        base_year=base_year,
        rolling_window=3,
    ).assign(prices="constant", base_year=base_year)

    constant_spending = pd.concat(
        [historical_constant, constant_projections], ignore_index=True
    )

    constant_data = targets.merge(
        constant_spending,
        on=["year", "donor_code"],
        how="left",
        suffixes=("", "_h"),
    )
    constant_data = constant_data.assign(oda=lambda d: d.oda_gni_ratio * d.gni)

    return constant_data.filter(
        [
            "year",
            "donor_code",
            "name_short",
            "oda_gni_ratio",
            "gni",
            "indicator",
            "oda",
            "prices",
        ]
    )


def load_and_prepare_data(
    start_year: int, end_year: int, base_year: int
) -> pd.DataFrame:
    """Loads EU spending projections and prepares the data with targets and ODA/GNI ratio.

    Returns:
        pd.DataFrame: DataFrame containing prepared data.
    """
    df = eu_spending_projections(
        start_year=start_year, end_year=end_year, base_year=base_year
    ).pipe(add_target_column)

    # Transform the target from percentage to absolute value
    df["target"] *= df["gni"]

    # Transform the ratio to percentage
    df["oda_gni_ratio"] *= 100
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renames columns to human-readable names.

    Args:
        df (pd.DataFrame): DataFrame to rename columns for.

    Returns:
        pd.DataFrame: DataFrame with renamed columns.
    """
    return df.rename(
        columns={
            "year": "Year",
            "oda_gni_ratio": "ODA/GNI ratio",
            "oda": "ODA",
            "target": "Target",
        }
    )


def filter_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Filters columns to keep only the required ones.

    Args:
        df (pd.DataFrame): DataFrame to filter.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    return df.filter(["Year", "Member State", "ODA/GNI ratio", "ODA", "Target", "gni"])


def calculate_eu_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates EU27 totals for ODA and GNI and appends them to the DataFrame.

    Args:
        df (pd.DataFrame): Original DataFrame with individual country data.

    Returns:
        pd.DataFrame: DataFrame with EU27 totals appended.
    """
    eu_totals = df.groupby("Year")[["ODA", "Target", "gni"]].sum().reset_index()
    eu_totals["Member State"] = "EU27 Countries"
    eu_totals["ODA/GNI ratio"] = 100 * eu_totals["ODA"] / eu_totals["gni"]

    return pd.concat([eu_totals, df], ignore_index=True).drop(columns=["gni"])


def clean_data_for_viz(df: pd.DataFrame) -> pd.DataFrame:
    """Rounds and calculates the missing target column, finalizing the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to finalize.

    Returns:
        pd.DataFrame: Finalized DataFrame.
    """
    df["ODA/GNI ratio"] = df["ODA/GNI ratio"].round(2)
    df["ODA"] = df["ODA"].round(0)
    df["Missing to target"] = (df["Target"] - df["ODA"]).clip(0).round(0)

    return df.drop(columns=["Target"])


def main_column_chart_with_projections(
    start_year: int = 2014, end_year: int = 2034, base_year: int = 2025
) -> pd.DataFrame:
    """Main processing function for ODA data.

    Returns:
        pd.DataFrame: Final DataFrame ready for output.
    """
    data = (
        load_and_prepare_data(
            start_year=start_year, end_year=end_year, base_year=base_year
        )
        .pipe(add_member_state_names)
        .pipe(rename_columns)
        .pipe(filter_columns)
        .sort_values(["Member State", "Year"])
        .pipe(calculate_eu_totals)
        .pipe(clean_data_for_viz)
    )

    return data


def calculate_mff_total_ms(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the total MFF contributions for each Member State.

    Args:
        df (pd.DataFrame): DataFrame with MFF contributions.

    Returns:
        pd.DataFrame: DataFrame with total MFF contributions for each Member State.
    """
    return (
        df.query("Year.between(2028,2034)")
        .groupby("Member State")["ODA"]
        .sum()
        .reset_index()
    )


if __name__ == "__main__":
    df = main_column_chart_with_projections()
    df.to_parquet(Paths.output / "eu27_chart.parquet")

    mff = calculate_mff_total_ms(df)
