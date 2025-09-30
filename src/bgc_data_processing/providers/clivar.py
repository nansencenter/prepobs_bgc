"""Specific parameters to load CLIVAR-provided data."""

from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="CLIVAR",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["CLIVAR"]["PATH"]),
    data_category=PROVIDERS_CONFIG["CLIVAR"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["CLIVAR"]["EXCLUDE"],
    files_pattern=FileNamePattern("clivar_({years})[0-9][0-9][0-9][0-9]_.*.csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("EXPOCODE"),
        date=VARS["date"].in_file_as("DATE"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("CTDPRS")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].in_file_as("CTDTMP"),
        salinity=VARS["salinity"].in_file_as(("CTDSAL", "CTDSAL_FLAG_W", [2])),
        oxygen=VARS["oxygen"]
        .in_file_as(("OXYGEN", "OXYGEN_FLAG_W", [2]))
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as(("PHSPHT", "PHSPHT_FLAG_W", [2]))
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as(("NITRAT", "NITRAT_FLAG_W", [2]))
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as(("SILCAT", "SILCAT_FLAG_W", [2]))
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].not_in_file(),
	ph=VARS["ph"].not_in_file(),
	dissolved_inorganic_carbon=VARS["dissolved_inorganic_carbon"].not_in_file(),
	total_alkalinity=VARS["total_alkalinity"].not_in_file(),
	pCO2=VARS["pCO2"].not_in_file(),
    bbp700=VARS["bbp700"].not_in_file(),
    poc = VARS["poc"].not_in_file(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
