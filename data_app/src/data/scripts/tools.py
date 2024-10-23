import pandas as pd
from bblocks import (
    WorldEconomicOutlook,
    set_bblocks_data_path,
    convert_id,
    add_short_names_column,
)
from oda_data import donor_groupings

from scripts import config

from pydeflate import deflate, set_pydeflate_path

set_bblocks_data_path(config.Paths.raw_data)
set_pydeflate_path(config.Paths.raw_data)

eu27 = list(donor_groupings()["eu27_countries"].keys())
eu28 = eu27 + [12]


def rebase_value(data: pd.DataFrame, year: int) -> pd.DataFrame:
    return data.assign(
        value=lambda d: d.groupby("dac_code")["value"].transform(
            lambda x: x / x.loc[d.year.dt.year == year].sum()
        )
    )


def add_dac_codes(data: pd.DataFrame) -> pd.DataFrame:
    data["dac_code"] = convert_id(
        data["iso_code"],
        "ISO3",
        "DACCode",
        not_found=pd.NA,
        additional_mapping={"EUI": 918},
    ).astype("Int32")
    return data


def get_constant_deflators(
    base: int = 2022, eu_list: list | None = None
) -> pd.DataFrame:
    if eu_list is None:
        eu_list = eu27
    weo = WorldEconomicOutlook(year=2024, release=2)

    weo.load_data(["NGDP_D", "NGDPD"])

    df = (
        weo.get_data("NGDPD")
        .pipe(add_dac_codes)
        .loc[lambda d: d.dac_code.isin(eu_list + [918])]
    )
    eu = (
        weo.get_data()
        .pipe(add_dac_codes)
        .loc[lambda d: d.dac_code.isin(eu_list + [918])]
    )

    eu = eu.pivot(
        index=["iso_code", "dac_code", "year"], columns="indicator", values="value"
    ).reset_index()

    eu["NGDPD_C"] = eu["NGDPD"] / (eu["NGDP_D"] / 100)

    eu = (
        eu.groupby(["year"], dropna=False, observed=True)[["NGDPD", "NGDPD_C"]]
        .sum()
        .reset_index()
        .assign(iso_code="EUI", dac_code=918, donor_code=918, indicator="NGDP_D")
        .assign(value=lambda d: 100 * d.NGDPD / d.NGDPD_C)
        .filter(["iso_code", "dac_code", "year", "indicator", "value"])
    )

    df = pd.concat([df, eu], ignore_index=True)

    df = df.pipe(rebase_value, year=base)

    return df.filter(["dac_code", "iso_code", "year", "value"])


def get_gdp_growth_factor(from_year: int):

    weo = WorldEconomicOutlook(year=2024, release=1)

    weo.load_data(["NGDP_R"])

    df = (
        weo.get_data()
        .sort_values(["iso_code", "year"])
        .assign(year=lambda d: d.year.dt.year)
        .pipe(add_dac_codes)
        .loc[lambda d: d.dac_code.isin(eu27 + [918])]
    )

    base_values = df.loc[lambda d: d.year == from_year].filter(
        ["iso_code", "dac_code", "value"]
    )

    df = df.merge(
        base_values, on=["iso_code", "dac_code"], suffixes=("", "_base"), how="left"
    )
    df["value"] = 1 + (df["value"] - df["value_base"]) / df["value_base"]

    return df.filter(["dac_code", "dac_code", "iso_code", "year", "value"])


def to_constant(
    df: pd.DataFrame,
    base_year: int = 2025,
    source_currency: str = "EUI",
    source_column: str = "total_oda_official_definition",
    target_column: str = "total_oda_official_definition",
    eu_list: list | None = None,
) -> pd.DataFrame:
    if base_year > 2023:
        deflators = get_constant_deflators(base=base_year, eu_list=eu_list).assign(
            year=lambda d: d.year.dt.year
        )
        deflate_year = 2023
    else:
        deflate_year = base_year

    df = deflate(
        df=df,
        base_year=deflate_year,
        deflator_source="oecd_dac",
        deflator_method="dac_deflator",
        exchange_source="oecd_dac",
        source_currency="USA" if source_currency == "USD" else source_currency,
        target_currency="EUI",
        id_column="donor_code",
        id_type="DAC",
        date_column="year",
        source_column=source_column,
        target_column=target_column,
    )

    if "gni" in df.columns:

        df = deflate(
            df=df,
            base_year=deflate_year,
            deflator_source="oecd_dac",
            deflator_method="dac_deflator",
            exchange_source="oecd_dac",
            source_currency="USA" if source_currency == "USD" else source_currency,
            target_currency="EUI",
            id_column="donor_code",
            id_type="DAC",
            date_column="year",
            source_column="gni",
            target_column="gni",
        )

    if base_year > 2023:
        df = df.merge(
            deflators,
            left_on=["year", "donor_code"],
            right_on=["year", "dac_code"],
            how="left",
        )

        df[target_column] = df[target_column] / df["value"]

    if "gni" in df.columns:
        df = df.assign(gni=lambda d: d.gni / d.value)

    return df.assign(prices="constant", base_year=base_year)


def extend_deflators_to_year(
    data: pd.DataFrame, last_year: int, rolling_window: int
) -> pd.DataFrame:
    """This function creates rows for each donor for the missing years between the
    max year in the data and the last year specified in the arguments. The value is
    rolling average of the previous 3 years"""

    def fill_with_rolling_average(
        idx, group: pd.DataFrame, rolling_window: int = 3
    ) -> pd.DataFrame:

        # calculate yearly diff
        group["yearly_diff"] = group["value"].diff()

        new_index = pd.Index(
            range(group.year.max() - rolling_window, last_year + 1), name="year"
        )

        new_df = group.set_index("year").reindex(new_index)
        new_df["yearly_diff"] = (
            new_df["yearly_diff"].rolling(window=rolling_window).mean()
        )
        new_df["yearly_diff"] = new_df["yearly_diff"].ffill()
        new_df["value"] = new_df.value.fillna(
            (new_df["value"].shift(1).ffill() + new_df["yearly_diff"].shift(1).cumsum())
        )

        new_df = new_df.drop(columns=["yearly_diff"])
        group = group.drop(columns=["yearly_diff"])

        new_df[["dac_code", "iso_code"]] = idx

        new_df = new_df.loc[lambda d: d.index > group.year.max()]

        group = group
        new_df = new_df.reset_index()

        group = pd.concat([group, new_df], ignore_index=False)
        return group

    try:
        data = data.assign(year=lambda d: d.year.dt.year)
    except AttributeError:
        pass

    dfs = []

    for group_idx, group_data in data.groupby(
        ["dac_code", "iso_code"], dropna=False, observed=True
    ):
        dfs.append(
            fill_with_rolling_average(
                idx=group_idx, group=group_data, rolling_window=rolling_window
            )
        )

    return pd.concat(dfs, ignore_index=True)


def add_member_state_names(df: pd.DataFrame) -> pd.DataFrame:
    """Adds member state short names to the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with donor codes.

    Returns:
        pd.DataFrame: DataFrame with member state names added.
    """
    return add_short_names_column(
        df=df, id_column="donor_code", id_type="DACCode", target_column="Member State"
    )
