"""Data selectors objects."""

import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from abfile import ABFileArchv, ABFileGrid
from sklearn.neighbors import NearestNeighbors

from bgc_data_processing.core.filtering import Constraints
from bgc_data_processing.core.io.savers import StorerSaver
from bgc_data_processing.core.loaders.abfile_loaders import ABFileLoader
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.storers import Storer
from bgc_data_processing.exceptions import (
    ABFileLoadingError,
    IncompatibleMaskShapeError,
    UnsupportedLoadingFormatError,
)
from bgc_data_processing.verbose import with_verbose

if TYPE_CHECKING:
    from bgc_data_processing.core.variables.sets import (
        LoadingVariablesSet,
        SourceVariableSet,
    )
    from bgc_data_processing.utils.dateranges import DateRangeGenerator
    from bgc_data_processing.utils.patterns import FileNamePattern


class SelectiveABFileLoader(ABFileLoader):
    """Load ABFile only on given points.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    category: str
        Category provider belongs to.
    exclude: list[str]
        Filenames to exclude from loading.
    variables : LoadingVariablesSet
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    grid_basename: str
        Basename of the ab grid grid file for the loader.
        => files are considered to be loaded over the same grid.
    """

    def __init__(
        self,
        provider_name: str,
        category: str,
        exclude: list[str],
        variables: "LoadingVariablesSet",
        grid_basename: str,
    ) -> None:
        super().__init__(
            provider_name=provider_name,
            category=category,
            exclude=exclude,
            variables=variables,
            grid_basename=grid_basename,
        )

    def _get_grid_field(self, variable_name: str, mask: "Mask") -> pd.Series:
        """Retrieve a field from the grid adfiles.

        Parameters
        ----------
        variable_name : str
            Name of the variable to retrieve.

        Returns
        -------
        pd.Series
            Values for this variable.

        Raises
        ------
        ABFileLoadingError
            If the variable does not exist in the dataset.
        """
        variable = self._variables.get(var_name=variable_name)
        data = None
        for alias in variable.aliases:
            name, flag_name, flag_values = alias
            if name in self.grid_file.fieldnames:
                # load data
                mask_2d: np.ma.masked_array = self.grid_file.read_field(name)
                data_2d: np.ndarray = mask_2d.filled(np.nan)
                data = mask(data_2d, name=variable.label)
                # load flag
                if flag_name is None or flag_values is None:
                    is_valid = self._set_index(pd.Series(True, index=mask.index))
                else:
                    mask_2d: np.ma.masked_array = self.grid_file.read_field(name)
                    flag_2d: np.ndarray = mask_2d.filled(np.nan)
                    flag_1d = mask(flag_2d, name=flag_name)
                    flag = pd.Series(flag_1d, name=variable.label)
                    is_valid = flag.isin(flag_values)
                # check flag
                data[~is_valid] = variable.default
                break
        if data is None:
            error_msg = (
                f"Grid File has no data for the variable {variable_name}."
                f"Possible fieldnames are {self.grid_file.fieldnames}."
            )
            raise ABFileLoadingError(error_msg)
        return data

    def _load_field(
        self,
        file: ABFileArchv,
        field_name: str,
        level: int,
        mask: "Mask",
    ) -> pd.Series:
        """Load a field from an abfile.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        field_name : str
            Name of the field to load.
        level : int
            Number of the level to load data from.

        Returns
        -------
        pd.Series
            Flatten values from the field.
        """
        mask_2d: np.ma.masked_array = file.read_field(fieldname=field_name, level=level)
        data_2d: np.ndarray = mask_2d.filled(np.nan)
        return mask(data_2d)

    def _load_one_level(
        self,
        file: ABFileArchv,
        level: int,
        lon: pd.Series,
        lat: pd.Series,
        mask: "Mask",
    ) -> pd.DataFrame:
        """Load data on a single level.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        level : int
            Number of the level to load data from.
        lon: pd.Series
            Longitude values series
        lat: pd.Series
            Latitude values series

        Returns
        -------
        pd.DataFrame
            Raw data from the level, for all variables of interest.
        """
        # already existing columns, from grid abfiles
        columns = [lon, lat]
        in_dset = self._variables.in_dset
        not_in_dset = [var for var in self._variables if var not in in_dset]
        for variable in in_dset:
            if variable.name == self._variables.longitude_var_name:
                continue
            if variable.name == self._variables.latitude_var_name:
                continue
            found = False
            for alias in variable.aliases:
                name, flag_name, flag_values = alias
                if name in self._get_fields_by_level(file, level):
                    # load data
                    field_df = self._load_field(
                        file=file,
                        field_name=name,
                        level=level,
                        mask=mask,
                    )
                    field_df = field_df.rename(variable.label)
                    # load valid indicator
                    field_valid = self._load_valid(file, level, flag_name, flag_values)
                    if field_valid is not None:
                        # select valid data
                        field_df[~field_valid] = variable.default
                    columns.append(field_df)
                    found = True
                    break
            if not found:
                not_in_dset.append(variable)
        # create missing columns
        for missing in not_in_dset:
            columns.append(self._create_missing_column(missing))
        return pd.concat(columns, axis=1)

    def load(
        self,
        filepath: Path | str,
        constraints: Constraints,
        mask: "Mask",
    ) -> pd.DataFrame:
        """Load a abfiles from basename.

        Parameters
        ----------
        filepath: Path | str
            Path to the basename of the file to load.
        constraints : Constraints, optional
            Constraints slicer.

        Returns
        -------
        pd.DataFrame
            DataFrame corresponding to the file.
        """
        self._index = mask.index
        basename = ABFileLoader.convert_filepath_to_basename(filepath)
        raw_data = self._read(basename=str(basename), mask=mask)
        # transform thickness in depth
        with_depth = self._create_depth_column(raw_data)
        # create date columns
        with_dates = self._set_date_related_columns(with_depth, basename)
        # converts types
        typed = self._convert_types(with_dates)
        # apply corrections
        corrected = self._correct(typed)
        # apply constraints
        constrained = constraints.apply_constraints_to_dataframe(corrected)
        return self.remove_nan_rows(constrained)

    def _read(self, basename: str, mask: "Mask") -> pd.DataFrame:
        """Read the ABfile using abfiles tools.

        Parameters
        ----------
        basename : str
            Basename of the file (no extension). For example, for abfiles
            'folder/file.2000_11_12.a' and 'folder/file.2000_11_12.b', basename is
            'folder/file.2000_11_12'.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns for all variables (whether it is in the
            dataset or not).
        """
        file = ABFileArchv(basename=basename, action="r")
        lon = self._get_grid_field(self._variables.longitude_var_name, mask=mask)
        lat = self._get_grid_field(self._variables.latitude_var_name, mask=mask)
        all_levels = []
        # Load levels one by one
        for level in file.fieldlevels:
            level_slice = self._load_one_level(
                file,
                level=level,
                lon=lon,
                lat=lat,
                mask=mask,
            )
            all_levels.append(level_slice)
        return pd.concat(all_levels, axis=0, ignore_index=False)

    @classmethod
    def from_abloader(
        cls,
        loader: ABFileLoader,
    ) -> "SelectiveABFileLoader":
        """Create a Selective loader based on an existing loader.

        Parameters
        ----------
        loader : ABFileLoader
            Loader to use as reference.

        Returns
        -------
        SelectiveABFileLoader
            Selective Loader.
        """
        return SelectiveABFileLoader(
            provider_name=loader.provider,
            category=loader.category,
            exclude=loader.excluded_filenames,
            variables=loader.variables,
            grid_basename=loader.grid_basename,
        )


class NearestNeighborStrategy:
    """Implement a closest point search using NearestNeighbor algorithm.

    Parameters
    ----------
    **model_kwargs:
        Additional arguments to pass to sklearn.neighbors.NearestNeighbors.
        The value of 'n_neighbors' while be overridden by 1.
    """

    _strategy_name: str = "Nearest Neighbor"

    def __init__(self, **model_kwargs) -> None:
        model_kwargs["n_neighbors"] = 1
        self.model_kwargs = model_kwargs

    @property
    def name(self) -> str:
        """Strategy name."""
        return self._strategy_name

    @with_verbose(
        trigger_threshold=2,
        message=f"Closest index selection using {_strategy_name} strategy.",
    )
    def get_closest_indexes(
        self,
        simulations_lat_lon: pd.DataFrame,
        observations_lat_lon: pd.DataFrame,
    ) -> pd.Series:
        """Find closest simulation point for each observation point.

        Parameters
        ----------
        simulations_lat_lon : pd.DataFrame
            DataFrame with longitude and latitude for each simulations point.
        observations_lat_lon : pd.DataFrame
            DataFrame with longitude and latitude for each observation point.

        Returns
        -------
        pd.Series
            Index of closest point for every observation point.
        """
        model = NearestNeighbors(**self.model_kwargs)
        # Transforming to radian for haversine metric compatibility
        sim_radians = simulations_lat_lon * np.pi / 180
        obs_radians = observations_lat_lon * np.pi / 180
        model.fit(X=sim_radians)
        closest = model.kneighbors(
            obs_radians,
            return_distance=False,
        )
        return pd.Series(closest.flatten(), index=observations_lat_lon.index)


class Mask:
    """Mask to apply to ABFiles to filter data while loading.

    Parameters
    ----------
    mask_2d : np.ndarray
        2D array to mask layers when loading them.
    index_2d : np.ndarray
        2D array of indexes to use to reindex the filtered array.

    Raises
    ------
    ValueError
        If the mask and the index have a different shape.
    """

    def __init__(self, mask_2d: np.ndarray, index_2d: np.ndarray) -> None:
        self._index_2d = index_2d
        self.mask = mask_2d

    @property
    def mask(self) -> np.ndarray:
        """2D boolean mask."""
        return self._mask

    @mask.setter
    def mask(self, mask_2d: np.ndarray) -> None:
        if mask_2d.shape != self._index_2d.shape:
            raise IncompatibleMaskShapeError(self._index_2d.shape, mask_2d.shape)
        self._mask = mask_2d
        self._index = pd.Index(self._index_2d[self._mask].flatten())

    @property
    def index(self) -> pd.Index:
        """Index for masked data reindexing.

        Returns
        -------
        pd.Index
            Data Index.
        """
        return self._index

    def __call__(self, data_2d: np.ndarray, **kwargs) -> pd.Series:
        """Apply mask to 2D data.

        Parameters
        ----------
        data_2d : np.ndarray
            Data to apply the mask to.
        **kwargs:
            Additional parameters to pass to pd.Series.
            The value of 'index' while be overridden by self._index.

        Returns
        -------
        pd.Series
            Masked data as a pd.Series with self._index as index.
        """
        kwargs["index"] = self._index
        return pd.Series(data_2d[self._mask].flatten(), **kwargs)

    def intersect(self, mask_array: np.ndarray) -> "Mask":
        """Intersect the mask with another (same-shaped) boolean array.

        Parameters
        ----------
        mask_array : np.ndarray
            Array to intersect with.

        Returns
        -------
        Mask
            New mask whith self._mask & mask_array as mask array.

        Raises
        ------
        IncompatibleMaskShapeError
            If mask_array has the wrong shape.
        """
        if mask_array.shape != self.mask.shape:
            raise IncompatibleMaskShapeError(self.mask.shape, mask_array.shape)
        return Mask(
            mask_2d=self._mask & mask_array,
            index_2d=self._index_2d,
        )

    @classmethod
    def make_empty(cls, grid: ABFileGrid) -> "Mask":
        """Create a Mask with all values True with grid size.

        Parameters
        ----------
        grid : ABFileGrid
            ABFileGrid to use to have the grid size.

        Returns
        -------
        Mask
            Mask with only True values.
        """
        return Mask(
            mask_2d=np.full((grid.jdm, grid.idm), True),
            index_2d=np.array(range(grid.jdm * grid.idm)),
        )


class Match:
    """Match between observation indexes and simulations indexes.

    Parameters
    ----------
    obs_closests_indexes : pd.Series
        Closest simulated point index Series.
        The index is supposed to correspond to observations' index.
    """

    index_simulated: str = "sim_index"
    index_observed: str = "obs_index"
    index_loaded: str = "load_index"

    def __init__(self, obs_closests_indexes: pd.Series) -> None:
        index_link = obs_closests_indexes.to_frame(name=self.index_simulated)
        index_link.index.name = self.index_observed
        index_link.reset_index(inplace=True)
        self.index_link = index_link

    @with_verbose(trigger_threshold=1, message="Matching indexes.")
    def match(self, loaded_df: pd.DataFrame) -> pd.DataFrame:
        """Transform the DataFrame index to link it to observations' index.

        Parameters
        ----------
        loaded_df : pd.DataFrame
            DataFrame to change the index of.

        Returns
        -------
        pd.DataFrame
            Copy of loaded_df with a modified index, which correspond to
            observations' index values.
        """
        loaded_index = pd.Series(loaded_df.index, name=self.index_simulated).to_frame()
        loaded_index.index.name = self.index_loaded
        loaded_index.reset_index(inplace=True)
        loaded_copy = loaded_df.copy()
        loaded_copy.index = loaded_index.index
        merge = pd.merge(
            left=loaded_index,
            right=self.index_link,
            left_on=self.index_simulated,
            right_on=self.index_simulated,
            how="left",
        )
        reshaped = loaded_copy.loc[merge[self.index_loaded], :]
        reshaped.index = merge[self.index_observed].values
        return reshaped


class SelectiveDataSource(DataSource):
    """Selective Data Source.

    Parameters
    ----------
    reference : pd.DataFrame
        Reference Dataframe (observations).
    strategy : NearestNeighborStrategy
        Closer point finding strategy.
    provider_name : str
        Name of the data provider.
    data_format : str
        Data format.
    dirin : Path | str
        Input data directory.
    data_category : str
        Category of the data.
    excluded_files : list[str]
        Files not to load.
    files_pattern : FileNamePattern
        Pattern to match to load files.
    variable_ensemble : SourceVariableSet
        Ensembles of variables to consider.
    """

    _loader: SelectiveABFileLoader

    def __init__(
        self,
        reference: "Storer",
        strategy: NearestNeighborStrategy,
        provider_name: str,
        data_format: str,
        dirin: Path | str,
        data_category: str,
        excluded_files: list[str],
        files_pattern: "FileNamePattern",
        variable_ensemble: "SourceVariableSet",
        **kwargs,
    ) -> None:
        super().__init__(
            provider_name,
            data_format,
            dirin,
            data_category,
            excluded_files,
            files_pattern,
            variable_ensemble,
            **kwargs,
        )
        self.reference = reference.data
        self.strategy = strategy
        self.grid = self.loader.grid_file

    def _build_loader(
        self,
        provider_name: str,
        excluded_files: list[str],
    ) -> "SelectiveABFileLoader":
        """Build the loader.

        Parameters
        ----------
        provider_name : str
            Name of the Data provider.
            !!! At the moment, it is only possible to use "abfiles".
        excluded_files : list[str]
            Files to exclude.

        Returns
        -------
        SelectiveABFileLoader
            Selective Loader.

        Raises
        ------
        UnsupportedLoadingFormatError
            If the file format is not supported.
        """
        if self._format == "abfiles":
            return SelectiveABFileLoader(
                provider_name=provider_name,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **self._read_kwargs,
            )
        raise UnsupportedLoadingFormatError(self._format)

    def get_coord(self, var_name: str) -> pd.Series:
        """Get a coordinate field from loader.grid_file.

        Parameters
        ----------
        var_name : str
            Name of the variable to retrieve.

        Returns
        -------
        pd.Series
            Loaded variable as pd.Series.

        Raises
        ------
        ABFileLoadingError
            If the variable dosn't exist in the grid file.
        """
        var = self.loader.variables.get(var_name)
        found = False
        for alias, _, _ in var.aliases:
            if alias in self.grid.fieldnames:
                mask_2d: np.ma.masked_array = self.grid.read_field(alias)
                found = True
                break
        if not found:
            error_msg = (
                f"Grid File has no data for the variable {var.name}."
                f"Possible fieldnames are {self.grid.fieldnames}."
            )
            raise ABFileLoadingError(error_msg)
        value = mask_2d.filled(np.nan)
        return pd.Series(value.flatten(), name=var.label)

    @with_verbose(trigger_threshold=2, message="Collecting grid file's indexes.")
    def get_x_y_indexes(self) -> tuple[pd.Series, pd.Series]:
        """Get x and y indexes.

        Returns
        -------
        tuple[pd.Series, pd.Series]
            X indexes series, Y indexes series.
        """
        y_coords, x_coords = np.meshgrid(range(self.grid.idm), range(self.grid.jdm))
        x_coords_series = pd.Series(x_coords.flatten())
        y_coords_series = pd.Series(y_coords.flatten())
        return x_coords_series, y_coords_series

    @with_verbose(trigger_threshold=1, message="Selecting Data.")
    def select(
        self,
        data_slice: pd.DataFrame,
    ) -> tuple["Mask", "Match"]:
        """Select closest points in an abfile using self.strategy.

        Parameters
        ----------
        data_slice: pd.DataFrame
            Sice of data to select from.

        Returns
        -------
        tuple[Mask, Match]
            Mask to use for loader, Match to link observations to simulations.
        """
        lat_series = self.get_coord(self.loader.variables.latitude_var_name)
        lon_series = self.get_coord(self.loader.variables.longitude_var_name)
        sims = pd.concat([lat_series, lon_series], axis=1)
        x_coords_series, y_coords_series = self.get_x_y_indexes()
        index = self.strategy.get_closest_indexes(
            simulations_lat_lon=sims,
            observations_lat_lon=data_slice[sims.columns],
        )
        indexes = np.array(range(self.grid.jdm * self.grid.idm))
        indexes_2d = indexes.reshape((self.grid.jdm, self.grid.idm))
        selected_xs = x_coords_series.loc[index.values]
        selected_ys = y_coords_series.loc[index.values]
        to_keep = np.full(shape=(self.grid.jdm, self.grid.idm), fill_value=False)
        to_keep[selected_xs, selected_ys] = True
        return Mask(to_keep, indexes_2d), Match(index)

    @staticmethod
    @with_verbose(trigger_threshold=0, message="Loading data from [filepath].")
    def parse_date_from_filepath(filepath: Path | str) -> dt.date:
        """Parse date from abfile basename.

        Parameters
        ----------
        filepath : Path | str
            File path.

        Returns
        -------
        dt.date
            Corresponding date.
        """
        basename = ABFileLoader.convert_filepath_to_basename(filepath)
        date_part_basename = Path(basename).name.split(".")[-1]
        date = dt.datetime.strptime(date_part_basename, "%Y_%j_%H")
        return date.date()

    def get_basenames(
        self,
        constraints: "Constraints",
    ) -> list[Path]:
        """Return basenames of files matching constraints.

        Parameters
        ----------
        constraints : Constraints
            Data constraints, only year constraint is used.

        Returns
        -------
        list[Path]
            List of basenames matching constraints.
        """
        date_label = self.loader.variables.get(
            self.loader.variables.date_var_name,
        ).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self.loader.is_file_valid
        return pattern_matcher.select_matching_filepath(
            research_directory=self.dirin,
        )

    def _create_storer(
        self,
        filepath: Path | str,
        constraints: "Constraints",
    ) -> "Storer":
        """Create storer method definition to shadow DataSource's method.

        Parameters
        ----------
        filepath : Path | str
            File path.
        constraints : Constraints
            Constraints.

        Returns
        -------
        Storer
            Storer.
        """

    def load_all(self, constraints: "Constraints") -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        date_var_name = self.loader.variables.date_var_name
        date_var_label = self.loader.variables.get(date_var_name).label
        filepaths = self.get_basenames(
            constraints,
        )
        datas: list[pd.DataFrame] = []
        for filepath in filepaths:
            date = self.parse_date_from_filepath(filepath=filepath)
            data_slice = self.reference[self.reference[date_var_label].dt.date == date]
            if data_slice.empty:
                continue
            mask, match = self.select(data_slice)
            sim_data = self.loader.load(
                filepath,
                constraints=constraints,
                mask=mask,
            )
            datas.append(match.match(sim_data))
        concatenated = pd.concat(datas, axis=0)
        storer = Storer(
            data=concatenated,
            category=self.loader.category,
            providers=[self.loader.provider],
            variables=self._store_vars,
        )
        self._insert_all_features(storer)
        self._remove_temporary_variables(storer)
        return storer

    def load_and_save(
        self,
        saving_directory: Path | str,
        dateranges_gen: "DateRangeGenerator",
        constraints: "Constraints",
    ) -> None:
        """Save all the data before saving it all in the saving directory.

        Parameters
        ----------
        saving_directory : Path | str
            Path to the directory to save in.
        dateranges_gen : DateRangeGenerator
            Generator to use to retrieve dateranges.
        constraints : Constraints
            Contraints ot apply on data.
        """
        storer = self.load_all(constraints=constraints)
        saver = StorerSaver(storer)
        saver.save_from_daterange(
            dateranges_gen=dateranges_gen,
            saving_directory=Path(saving_directory),
        )

    @classmethod
    def from_data_source(
        cls,
        reference: Storer,
        strategy: NearestNeighborStrategy,
        dsource: DataSource,
    ) -> "SelectiveDataSource":
        """Create the sleective data source from an existing data source.

        Parameters
        ----------
        reference : Storer
            Reference Dataframe (observations).
        strategy : NearestNeighborStrategy
            Closer point finding strategy.
        dsource : DataSource
            Template DataSource

        Returns
        -------
        SelectiveDataSource
            Selective datasource from Template.
        """
        return cls(
            reference=reference,
            strategy=strategy,
            **dsource.as_template,
        )
