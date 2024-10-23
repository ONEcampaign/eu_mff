import pandas as pd
from oda_data import ODAData, set_data_path
from oda_reader import download_dac1

from scripts import config
from scripts.tools import to_constant

set_data_path(config.Paths.raw_data)

from scripts.common import EU27, EU28


def get_eui_total_oda(
    start_year: int = 2022, end_year: int = 2023, currency: str = "USD"
) -> pd.DataFrame:

    oda = ODAData(
        years=range(start_year, end_year + 1),
        donors=[20918, 918],
        currency=currency,
    )

    oda.load_indicator(["total_oda_official_definition"])

    df = (
        oda.get_data()
        .pivot(index=["year", "donor_code"], columns="indicator", values="value")
        .reset_index()
    )

    return df


def download_eu_x_eui(
    x: list = EU27, start_year: int = 2022, end_year: int = 2023
) -> pd.DataFrame:

    filters = {
        "flow_type": "1120",
        "measure": "2102",
        "price_base": "V",
        "unit_measure": "USD",
    }
    df = download_dac1(start_year=start_year, end_year=end_year, filters=filters)

    df = df.loc[lambda d: d.donor_code.isin(x)]

    return df


def contributions_to_constant(df: pd.DataFrame, eu_list: list) -> pd.DataFrame:
    return to_constant(
        df=df,
        base_year=2025,
        source_currency="USD",
        source_column="value_eu",
        target_column="value_eu",
        eu_list=eu_list,
    )


def eu_own_resources_constant_eur() -> pd.DataFrame:
    spending_eui = get_eui_total_oda(
        start_year=2014, end_year=2023, currency="USD"
    ).assign(dac_code=lambda d: d.donor_code)

    spending_eui = to_constant(df=spending_eui, base_year=2025, source_currency="USD")

    eu28_contributions_to_eui = (
        download_eu_x_eui(EU28, start_year=2014, end_year=2020)
        .rename(columns={"value": "value_eu"})
        .pipe(contributions_to_constant, eu_list=EU28)
    )

    eu27_contributions_to_eui = (
        download_eu_x_eui(EU27, start_year=2021, end_year=2023)
        .rename(columns={"value": "value_eu"})
        .pipe(contributions_to_constant, eu_list=EU27)
    )

    contributions_to_eui = (
        pd.concat(
            [eu28_contributions_to_eui, eu27_contributions_to_eui], ignore_index=True
        )
        .groupby("year", dropna=False, observed=True)["value_eu"]
        .sum()
        .reset_index()
    )

    data = pd.merge(spending_eui, contributions_to_eui, on="year", how="left")

    data["own_resources"] = data["total_oda_official_definition"] - data["value_eu"]

    data["own_resources_share"] = (
        100 * data["own_resources"] / data["total_oda_official_definition"]
    )

    return data


def eui_spending_chart(members: pd.DataFrame) -> pd.DataFrame:

    members = members.query("`Member State` == 'EU27 Countries'")

    data = eu_own_resources_constant_eur().filter(
        [
            "year",
            "total_oda_official_definition",
            "own_resources",
            "value_eu",
        ]
    )

    data = data.merge(members, left_on="year", right_on="Year", how="left")
    data["Member States"] = data["ODA"] - data["value_eu"]

    data = data.filter(["year", "Member States", "own_resources", "value_eu"])

    data = data.rename(
        columns={
            "own_resources": "Non-imputable EU Institutions ODA",
            "value_eu": "Imputable EU Institutions ODA",
        }
    )

    return data


def eui_key_numbers(data: pd.DataFrame, period_start: int, period_end: int) -> dict:

    df = data.loc[lambda d: d.year.between(period_start, period_end)]
    ms_only = round(df["Member States"].sum(), 1)
    imputable = round(df["Imputable EU Institutions ODA"].sum(), 1)
    non_imputable = round(df["Non-imputable EU Institutions ODA"].sum(), 1)

    ms_total = round(ms_only + imputable, 1)
    eui_total = round(imputable + non_imputable, 1)

    non_imputable_share_of_eu = round(100 * non_imputable / eui_total, 4)
    eu_imputable_share_of_ms_total = round(100 * imputable / ms_total, 4)

    numbers = {
        "MS only": ms_only,
        "Imputable EU Institutions": imputable,
        "Non-imputable EU Institutions": non_imputable,
        "MS total": ms_total,
        "EUI total": eui_total,
        "Non-imputable share of EUI": non_imputable_share_of_eu,
        "Imputable share of MS total": eu_imputable_share_of_ms_total,
    }

    return numbers


def eui_mff_period(
    ms_data: pd.DataFrame,
    eui_data: pd.DataFrame,
    start_year: int = 2028,
    end_year: int = 2034,
) -> tuple[float, float]:

    data = ms_data.loc[lambda d: d.Year.between(start_year, end_year)]
    eui_numbers = eui_key_numbers(eui_data, 2014, 2022)

    ms_mff = data.loc[lambda d: d["Member State"] == "EU27 Countries", "ODA"].sum()
    eui_imputable = ms_mff * eui_numbers["Imputable share of MS total"] / 100
    eui_non_imputable = (
        eui_imputable / (1 - eui_numbers["Non-imputable share of EUI"] / 100)
        - eui_imputable
    )

    return eui_imputable, eui_non_imputable


if __name__ == "__main__":
    # Read MS chart data
    ms = pd.read_parquet(config.Paths.app_data / "eu27_chart.parquet")
    # Calculate EUI spending chart
    eui = eui_spending_chart(ms)
    # Save for Flourish
    eui.to_csv(config.Paths.app_data / "eui_spending_chart.csv", index=False)

    # Calculate key numbers.
    imputable, non_imputable = eui_mff_period(ms, eui)
    total_eui = imputable + non_imputable
