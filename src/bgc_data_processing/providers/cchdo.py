"""Specific parameters to load CCHDO-provided data."""

from pathlib import Path

import numpy as np

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="CCHDO",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["CCHDO"]["PATH"]),
    data_category=PROVIDERS_CONFIG["CCHDO"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["CCHDO"]["EXCLUDE"],
    files_pattern=FileNamePattern(".*.nc"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("expocode"),
        date=VARS["date"].in_file_as("time"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("longitude"),
        latitude=VARS["latitude"].in_file_as("latitude"),
        depth=VARS["depth"]
        .in_file_as("pressure")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=VARS["temperature"].in_file_as("ctd_temperature"),
        salinity=VARS["salinity"].in_file_as(
            ("bottle_salinity", "bottle_salinity_qc", [1]),
            ("ctd_salinity", "ctd_salinity_qc", [1]),
        ),
        oxygen=VARS["oxygen"].in_file_as(
            ("oxygen", "oxygen_qc", [1]),
            ("ctd_oxygen", "ctd_oxygen_qc", [1])
        )
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"].in_file_as(
            ("phosphate", "phosphate_qc", [1])
        ),
        nitrate=VARS["nitrate"].in_file_as(
            ("nitrate", "nitrate_qc", [1])
        ),
        silicate=VARS["silicate"].in_file_as(
            ("silicate", "silicate_qc", [1])
        ),
        chlorophyll=VARS["chlorophyll"].not_in_file(),
    ),
)
