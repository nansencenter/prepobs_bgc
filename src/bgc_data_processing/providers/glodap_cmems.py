"""Specific parameters to load GLODAPv2.2023-provided data."""

from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="GLODAP_CMEMS",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["GLODAP_CMEMS"]["PATH"]),
    data_category=PROVIDERS_CONFIG["GLODAP_CMEMS"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["GLODAP_CMEMS"]["EXCLUDE"],
    files_pattern=FileNamePattern(".*-GLODAPv22023.nc"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].not_in_file(),
        date=VARS["date"].in_file_as("TIME"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("DEPH")
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].in_file_as(("TEMP", "TEMP_QC", [1])),
        salinity=VARS["salinity"].in_file_as(("PSAL", "PSL_QC", [1])),
        oxygen=VARS["oxygen"]
        .in_file_as("DOX2")
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as("PHOW")
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as("NTAW")
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as("SLCW")
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].in_file_as(("CPHL", "CPHL_QC", [1])),
	ph=VARS["ph"].in_file_as(("PHPH", "PHPH_QC", [1])),
	dissolved_inorganic_carbon=VARS["dissolved_inorganic_carbon"]
        .in_file_as(("TICW", "TICW_QC", [1])),
	total_alkalinity=VARS["total_alkalinity"]
        .in_file_as(("ALKW", "ALKW_QC", [1])),
	pCO2=VARS["pCO2"].not_in_file(),
    bbp700=VARS["bbp700"].not_in_file(),
    poc = VARS["poc"].not_in_file(),
    ),
    
)