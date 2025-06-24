# CHAZ Wind Hazard Maps

This repository documents a CLIMADA‑compatible workflow that converts CHAZ tropical‑cyclone event sets into gridded wind‑hazard layers and summary figures, reproducible on an HPC cluster or a local workstation.

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