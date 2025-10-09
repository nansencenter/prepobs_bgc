\# Tools

This directory includes Python scripts and configuration files designed to:



\- \*\*Download GLODAP data from the Copernicus Marine Environment Monitoring Service (CMEMS)\*\*

\- \*\*Create a new BGC-Argo dataset with Particulate Organic Carbon (POC) computed\*\*



The resulting datasets can be processed and aggregated through the `prepobs\_bgc` package, using the dedicated providers `GLODAP\_CMEMS` and `SUBSET\_BGC\_ARGO\_DAC\_POC`.



\## Installation \& Requirements

Before running any script, ensure that:



1\. The same \*\*conda environment\*\* used for the main `prepobs\_bgc` package is activated.



For \*\*GLODAP data download\*\*, make sure that: 



2\. The \[\*\*CMEMS toolbox\*\*](https://help.marine.copernicus.eu/en/articles/7970514-copernicus-marine-toolbox-installation) is installed in your environment:



```bash

conda install conda-forge::copernicusmarine --yes

```

3\. You have a registered \*\*CMEMS account\*\* (Required to use the CMEMS Toolbox)

4\. Your \*\*CMEMS credentials\*\* are correctly filled in `config\_user\_template.yaml`.



\## Contents



\#### 1. `cmems\_carbon\_loader.py`



This script is used to download \[\*\*GLODAP observational data\*\*](https://data.marine.copernicus.eu/product/INSITU\_GLO\_BGC\_CARBON\_DISCRETE\_MY\_013\_050/download?dataset=cmems\_obs-ins\_glo\_bgc-car\_my\_glodap-obs\_irr\_202211) from \*\*CMEMS\*\* using the Copernicus Marine toolbox.



\- \*\*Input:\*\* 

&nbsp;   - CMEMS credentials (`config\_user\_template.yaml`) 

&nbsp;   - Product ID, here `cmems\_obs-ins\_glo\_bgc-car\_my\_glodap-obs\_irr`

\- \*\*Output:\*\*  

&nbsp;   - A text file listing all selected GLODAP NetCDF files (`GLODAP\_download\_list\_<year>.txt`)

&nbsp;   - If isload=True: Netcdf files are downloaded into `data/CMEMS\_carbon\_<year>\_<dataset\_version>/`



\- \*\*Usage:\*\* 

&nbsp;   - `<year>` → last year of the period to download (format: YYYY)

&nbsp;   - `<isload>` → `True` to download files, `False` to only create the file list

```bash

python cmems\_carbon\_loader.py <year> <isload>

```







Adjust the temporal and spatial filters in the bbox dictionary (line 128) if you need a region other than the Arctic or a start year other than 1997.



The structure of the code was inspired by existing data download scripts in the \[`TOPAZ\_RAN\_BIORAN\_v2`](https://github.com/nansencenter/TOPAZ\_RAN\_BIORAN\_v2) package from NERSC.





\#### 2. `config\_user\_template.yaml`

Template for CMEMS credentials.



Replace the placeholders with your personal CMEMS account information:  



```bash

username=your\_cmems\_username

password=your\_cmems\_password

```



Do not share this file or commit it to the repository, the credentials are confidential.







\#### 3. `POC\_computation.py`

Script to compute Particulate Organic Carbon (POC) from BGC-Argo observations.

If both chlorophyll and backscattering at 700 nm are present and of good quality, the script estimates POC using the \*\*Koestner et al. (2024)\*\* empirical model (model B).



\- \*\*Input:\*\* 

&nbsp;   - BGC-Argo NetCDF dataset

&nbsp;   - Variables to keep from the original dataset

\- \*\*Output:\*\* A subset dataset including computed POC values

\- \*\*Usage:\*\*

```bash

python POC\_computation.py

```



\#### 4. `Function\_POC.py`





This script provides the implementation of the \[Koestner et al. (2024)](https://doi.org/10.3389/fmars.2023.1197953) Model B for computing POC from BGC-ARGO measurements of backscattering at 700 nm (bbp) and chlorophyll-a concentration (chl-a). It was implemented in Python by Juliano Ramanantsoa and reused here without modification.



\- The function `Koest23\_modelB\_700p()` returns:

&nbsp;   - The estimated POC concentration (mg m⁻³)

&nbsp;   - Its prediction interval

&nbsp;   - The chl-a/bbp ratio (comp) used in the model





\## Reference

Koestner, D., Stramski, D., \& Reynolds, R. A. (2024). \[\*Improved multivariable algorithms for estimating oceanic particulate organic carbon concentration from optical backscattering and chlorophyll-a measurements.\*](https://doi.org/10.3389/fmars.2023.1197953) \*\*Frontiers in Marine Science\*\*, 10:1197953. 







\## Author



This work was carried out as part of a Master’s internship at the

Nansen Environmental and Remote Sensing Center (NERSC), Bergen, Norway.



\- \*\*Author:\*\* \[Kim Monoury--Homet](https://github.com/KimMonouryHomet)

\- \*\*Supervisor:\*\* \[Tsuyoshi Wakamatsu](https://github.com/tsuyoshiwakamatsu)





