"""Specific parameters to load coArgo-provided data."""

from pathlib import Path
import numpy as np

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern


loader = DataSource(
    provider_name="ARGO_DAC",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["ARGO_DAC"]["PATH"]),
    data_category=PROVIDERS_CONFIG["ARGO_DAC"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["ARGO_DAC"]["EXCLUDE"],
    files_pattern=FileNamePattern(".*.nc"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].not_in_file(),
        date = VARS["date"].in_file_as("JULD"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("PRES_ADJUSTED")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=VARS["temperature"].in_file_as(
            ("TEMP_ADJUSTED", "TEMP_ADJUSTED_QC", ["1", "2", "5","8"]), 
            ("TEMP", "TEMP_QC", ["1", "2", "5","8"]),
        ),
        salinity=VARS["salinity"].in_file_as(
            ("PSAL_ADJUSTED", "PSAL_ADJUSTED_QC", ["1", "2", "5","8"]), 
            ("PSAl", "PSAl_QC", ["1", "2", "5","8"]),
        ),
        oxygen=VARS["oxygen"].not_in_file(),
        phosphate=VARS["phosphate"].not_in_file(),
        nitrate=VARS["nitrate"].not_in_file(),
        silicate=VARS["silicate"].not_in_file(),
        chlorophyll=VARS["chlorophyll"].not_in_file(),
	ph=VARS["ph"].not_in_file(),
	dissolved_inorganic_carbon=VARS["dissolved_inorganic_carbon"].not_in_file(),
	total_alkalinity=VARS["total_alkalinity"].not_in_file(),
	pCO2=VARS["pCO2"].not_in_file(),
    bbp700=VARS["bbp700"].not_in_file(),
    poc = VARS["poc"].not_in_file(),
    ),
)
