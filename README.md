# CHAZ Wind Hazard Maps

This repository documents a CLIMADA‑compatible workflow that converts CHAZ tropical‑cyclone event sets into gridded wind‑hazard layers and summary figures, reproducible on an HPC cluster or a local workstation.
```
CHAZ-hazard-maps/
│
├── README.md                 ← you are here
├── LICENSE                   ← GPL-3.0
├── .gitignore                ← ignores __pycache__, *.pyc, .DS_Store, more_scripts/
│
├── CHAZ-pre-processing/              ← scripts for frequency bias correction and preprocessing - requires HPC cluster
│   ├── compute_era5_windfields.py    ← compute historical (ERA5) windfields (see Meiler et al., 2022)
│   ├── concat_freq_corr_era5.py      ← merge and frequency correct ERA5 windfields
│   ├── freq_corr_era5.py             ← apply frequency bias correction to ERA5 windfields
│   └── freq_corr.py                  ← apply frequency bias correction to GCM-derived windfields (see Meiler et al., 2025)
│
├── main/                                            ← scripts for map generation - requires HPC cluster
│   ├── compute_exceedance.py                        ← exceedance intensity maps for single GCMs
│   ├── compute_return_periods.py                    ← return period maps for single GCMs
│   ├── compute_exceedance_intensity_era5_parallel.py← historical (ERA5) exceedance intensity maps, run in parallel
│   ├── compute_return_periods_era5_parallel.py      ← historical (ERA5) return period maps, run in parallel
│   ├── compute_combined_exceedance_intensity_parallel.py ← multi‑model exceedance intensity maps
│   ├── compute_combined_return_periods_parallel.py  ← multi‑model return period maps
│   ├── combine_tiles.py                             ← merge tiles for ERA5 output, from parallel runs
│   ├── combine_all-model_tiles.py                   ← merge tiles for multi‑model output, from parallel
│   └── hazard_map_utils.py                          ← helper functions for NetCDF/GeoDataFrame I/O
│
├── output/                   ← generating figures & tables for publication
│   ├── plot_rp_maps.py
│   └── plot_summary_panels.py
│
└── data/                     ← output files used for figures & tables
    ├── basins.geojson        ← tbd
    └── world_grid_10km.nc    ← tbd
```


### Prerequisites

#### CLIMADA

The workflow relies on CLIMADA v4.x (⟨https://github.com/CLIMADA‑project/climada_python⟩).

#### Additional Python Packages

All other dependencies (e.g., xarray, geopandas, cartopy) are already included in the CLIMADA environment.

#### CHAZ Event Sets

Raw CHAZ CMIP6 event files (≈ 7 TB) are not hosted in this repo.  Request access from the original authors: https://github.com/cl3225/CHAZ



### Citing This Work

If you use this code or the derived maps, please cite:

Meiler, S. et al. (2025) Global tropical‑cyclone wind hazard maps derived from CHAZ event sets. Scientific Data. https://doi.org/10.XXXX/XXXXX

and the underlying CHAZ and CLIMADA references.
