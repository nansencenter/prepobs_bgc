# Density Plotting

`make run-plot-data-density`
## Summary

This scripts reads data from a folder and displays the data density on a map.

## Configuration

The configuration file for this script is `config/plot_data_density.toml` (based on [`config/default_plot_data_density.toml`]({{repo_blob}}/config/default/plot_data_density.toml)). All the parameters and their functionality are listed below:
### **Input/output**
??? question "LOADING_DIR"
    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SAVE"
    Whether to save the figure or not.

    **default**: `true`

    Expected type: `bool`

??? question "SAVING_DIR"
    Directory in which to save the figure.

    **default**: `"bgc_figs"`

    Expected type: `str`

??? question "SHOW"
    Whether to show the figure or not.

    **default**: `true`

    Expected type: `bool`

??? question "VARIABLE"
    Name of the variable to map. The names are supposed to be the ones defined in `config/variables.toml` ([`config/default/variables.toml`]({{repo_blob}}/config/default/variables.toml)) by default.). If 'all': will map density of datapoints, regardless of their variables.

    **default**: `"all"`

    Expected type: `str`
### **Data Selection**
??? question "DATE_MIN"
    First date to map (included).

    **default**: `"20070101"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "DATE_MAX"
    Last date to map (included).

    **default**: `"20201231"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "LATITUDE_MIN"
    Minimum latitude boundary to consider for the loaded data (included).

    **default**: `50`

    Expected type: `int or float`

??? question "LATITUDE_MAX"
    Maximum latitude boundary to consider for the loaded data (included).

    **default**: `90`

    Expected type: `int or float`

??? question "LONGITUDE_MIN"
    Minimum longitude boundary to consider for the loaded data (included).

    **default**: `-180`

    Expected type: `int or float`

??? question "LONGITUDE_MAX"
    Maximum longitude boundary to consider for the loaded data (included).

    **default**: `180`

    Expected type: `int or float`

??? question "LATITUDE_MAP_MIN"
    Minimum latitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe.

    **default**: `nan`

    Expected type: `int or float`

??? question "DEPTH_MIN"
    Minimum depth boundary to consider for the loaded data (included).

    **default**: `nan`

    Expected type: `int or float`

??? question "DEPTH_MAX"
    Maximum depth boundary to consider for the loaded data (included).

    **default**: `0`

    Expected type: `int or float`

??? question "EXPOCODES_TO_LOAD"
    Precise expocode to load alone. If empty, no discrimination on expocode will be conducted.

    **default**: `[]`

    Expected type: `list[str]`

??? question "PRIORITY"
    Providers priority list to use when removing duplicates. Every provider takes priority over the following ones.

    **default**: `["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]`

    Expected type: `list[str]`
### **Mapping Options**
??? question "LATITUDE_MAP_MAX"
    Maximum latitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe.

    **default**: `nan`

    Expected type: `int or float`

??? question "LONGITUDE_MAP_MIN"
    Minimum longitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe.

    **default**: `nan`

    Expected type: `int or float`

??? question "LONGITUDE_MAP_MAX"
    Maximum longitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe.

    **default**: `nan`

    Expected type: `int or float`

??? question "BIN_SIZE"
    Bins size. If list, first component is latitude size, second is longitude size. If int or float, represents both latitude and longitude size.

    **default**: `[0.5, 1.5]`

    Expected type: `list[float] or list[int] or float or int`

??? question "CONSIDER_DEPTH"
    If `true`: the plotted density will consider all data points (even the ones in the water column). If `false`: the plotted density will only consider one data point per location and date.

    **default**: `false`

    Expected type: `bool`
### **Others**
??? question "VERBOSE"
    Verbose value, the higher, the more informations. If set to 0 or below: no information displayed. If set to 1: minimal informations displayed. If set to 2: very complete informations displayed. If set to 3 or higher: exhaustive informations displayed.

    **default**: `2`

    Expected type: `int`
## Script Output

When executed, this script display a map with the density of the data points (regrouped in bins).

This is an example of what this map could look like:

![plot mesh output example]({{fix_url("assets/plots/mesh.png")}}){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/plot_data_density.py)
