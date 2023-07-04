"""Objects related to water masses."""
from collections.abc import Iterable

import numpy as np
import pandas as pd

from bgc_data_processing.core.filtering import Constraints
from bgc_data_processing.core.storers import Storer
from bgc_data_processing.core.variables.vars import NotExistingVar


class WaterMass:
    """Water Mass.

    Parameters
    ----------
    name : str
        Water mass name.
    ptemperature_range : Iterable[float, float], optional
        Potential temperature range: (minimum, maximum), by default (np.nan, np.nan)
    salinity_range : Iterable[float, float], optional
        Salinity range: (minimum, maximum), by default (np.nan, np.nan)
    sigma_t_range : Iterable[float, float], optional
        Sigma-t range: (minimum, maximum), by default (np.nan, np.nan)
    """

    def __init__(
        self,
        name: str,
        acronym: str | None = None,
        ptemperature_range: Iterable[float, float] = (np.nan, np.nan),
        salinity_range: Iterable[float, float] = (np.nan, np.nan),
        sigma_t_range: Iterable[float, float] = (np.nan, np.nan),
    ) -> None:
        self.name = name
        if acronym is None:
            acronym = "".join(word[0].upper() for word in name.split(" "))
        self.acronym = acronym
        self.ptemperature_min = ptemperature_range[0]
        self.ptemperature_max = ptemperature_range[1]
        self.salinity_min = salinity_range[0]
        self.salinity_max = salinity_range[1]
        self.sigma_t_min = sigma_t_range[0]
        self.sigma_t_max = sigma_t_range[1]

    def __repr__(self) -> str:
        """Represent self as a string.

        Returns
        -------
        str
            Name and boundaries.
        """
        name_txt = f"{self.name} ({self.acronym})"
        temp_txt = f"PTemperature in [{self.ptemperature_min},{self.ptemperature_max}]"
        saln_txt = f"Salinity in [{self.salinity_min},{self.salinity_max}]"
        sigt_txt = f"Sigma-t in [{self.sigma_t_min},{self.sigma_t_max}]"
        return f"{name_txt}\n{temp_txt}\n{saln_txt}\n{sigt_txt}"

    def make_constraints(
        self,
        ptemperature_label: str,
        salinity_label: str,
        sigma_t_label: str,
    ) -> Constraints:
        """Create the constraint for the water mass.

        Parameters
        ----------
        ptemperature_label : str
            Potential temperature label.
        salinity_label : str
            Salinity label.
        sigma_t_label : str
            Sigma-t label.

        Returns
        -------
        Constraints
            Constraint corresponding to the water mass.
        """
        constraints = Constraints()
        constraints.add_boundary_constraint(
            field_label=ptemperature_label,
            minimal_value=self.ptemperature_min,
            maximal_value=self.ptemperature_max,
        )
        constraints.add_boundary_constraint(
            field_label=salinity_label,
            minimal_value=self.salinity_min,
            maximal_value=self.salinity_max,
        )
        constraints.add_boundary_constraint(
            field_label=sigma_t_label,
            minimal_value=self.sigma_t_min,
            maximal_value=self.sigma_t_max,
        )
        return constraints

    def extract_from_storer(
        self,
        storer: "Storer",
        ptemperature_name: str,
        salinity_name: str,
        sigma_t_name: str,
    ) -> "Storer":
        """Extract a the storer whose values are in the water mass.

        Parameters
        ----------
        storer : Storer
            Original Storer.
        ptemperature_name : str
            Potenital temperature variable name.
        salinity_name : str
            Salinity Variable name.
        sigma_t_name : str
            Sigma-t variable name.

        Returns
        -------
        Storer
            Storer whose values are in the water mass.
        """
        constraints = self.make_constraints(
            ptemperature_label=storer.variables.get(ptemperature_name).label,
            salinity_label=storer.variables.get(salinity_name).label,
            sigma_t_label=storer.variables.get(sigma_t_name).label,
        )
        return constraints.apply_constraints_to_storer(storer)

    def flag_in_storer(
        self,
        original_storer: "Storer",
        water_mass_variable_name: str,
        ptemperature_name: str,
        salinity_name: str,
        sigma_t_name: str,
        create_var_if_missing: bool = True,
    ) -> "Storer":
        """Flag the.

        Parameters
        ----------
        original_storer : Storer
            original storer.
        water_mass_variable_name : str
            Name of the water mass variable.
        ptemperature_name : str
            Potential temperature variable name.
        salinity_name : str
            Salinity Variable name.
        sigma_t_name : str
            Sigma-t at pressure 0 variable name.
        create_var_if_missing : bool, optional
            Whether to create the water mass variable in the storer., by default True

        Returns
        -------
        Storer
            Copy of original storer with an updated 'water mass' field.

        Raises
        ------
        ValueError
            If the water mass variable doens't exists and can't be created.
        """
        constraints = self.make_constraints(
            ptemperature_label=original_storer.variables.get(ptemperature_name).label,
            salinity_label=original_storer.variables.get(salinity_name).label,
            sigma_t_label=original_storer.variables.get(sigma_t_name).label,
        )
        full_data = original_storer.data
        compliant = constraints.apply_constraints_to_dataframe(full_data).index
        if original_storer.variables.has_name(water_mass_variable_name):
            water_mass_var = original_storer.variables.get(water_mass_variable_name)
            water_mass_label = water_mass_var.label
            data = full_data[water_mass_label]
            data[compliant] = self.name
            full_data[water_mass_label] = data
            return Storer(
                data=full_data,
                category=original_storer.category,
                providers=original_storer.providers[:],
                variables=original_storer.variables,
            )
        if not create_var_if_missing:
            error_msg = f"{water_mass_variable_name} invalid for the given storer."
            raise ValueError(error_msg)

        data = pd.Series(np.nan, index=full_data.index)
        data[compliant] = self.name
        new_var = NotExistingVar(
            water_mass_variable_name,
            "[]",
            str,
            np.nan,
            "%-15s",
            "%15s",
        )
        new_storer = Storer(
            data=full_data,
            category=original_storer.category,
            providers=original_storer.providers[:],
            variables=original_storer.variables,
        )
        new_storer.add_feature(new_var, data)
        return new_storer
