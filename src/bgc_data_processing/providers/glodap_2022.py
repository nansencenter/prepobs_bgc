"""Specific parameters to load GLODAPv2.2022-provided data."""

from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="GLODAP_2022",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["GLODAP_2022"]["PATH"]),
    data_category=PROVIDERS_CONFIG["GLODAP_2022"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["GLODAP_2022"]["EXCLUDE"],
    files_pattern=FileNamePattern("GLODAPv2.2022_all.csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("G2expocode"),
        date=VARS["date"].not_in_file(),
        year=VARS["year"].in_file_as("G2year"),
        month=VARS["month"].in_file_as("G2month"),
        day=VARS["day"].in_file_as("G2day"),
        hour=VARS["hour"].in_file_as("G2hour"),
        longitude=VARS["longitude"].in_file_as("G2longitude"),
        latitude=VARS["latitude"].in_file_as("G2latitude"),
        depth=VARS["depth"]
        .in_file_as("G2depth")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].in_file_as("G2temperature"),
        salinity=VARS["salinity"].in_file_as(
            ("G2salinity", "G2salinityf", [2]),
        ),
        oxygen=VARS["oxygen"]
        .in_file_as(("G2oxygen", "G2oxygenf", [2]))
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as(("G2phosphate", "G2phosphatef", [2]))
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as(("G2nitrate", "G2nitratef", [2]))
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as(("G2silicate", "G2silicatef", [2]))
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },
)
