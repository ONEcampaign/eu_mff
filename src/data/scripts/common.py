from oda_data import donor_groupings

CURRENCY = "EUR"
EU27 = list(donor_groupings()["eu27_countries"].keys())
EU28 = EU27 + [12]
LOWER_TARGET = 0.0033
TARGET = 0.007
LOWER_TARGET_COUNTRIES = {
    30,
    69,
    75,
    77,
    72,
    62,
    61,
    68,
    45,
    82,
    84,
    83,
    76,
}
