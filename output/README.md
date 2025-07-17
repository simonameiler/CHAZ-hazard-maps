# CHAZ Hazard Maps: Global coastal wind hazard maps from the CHAZ tropical cyclone model

## Folder Structure Overview

The dataset is organized first by hazard metric (`exceedance_intensity` or `return_periods`), then by file format (`csv`, `nc`, or `raster.nc`). Within each format, files are grouped as follows:

- `ERA5/`: Historical baseline based on ERA5 reanalysis
- `per-GCM/<GCM>/sspXXX/`: Individual GCM simulations grouped by GCM and SSP

## Folder Details

- `return_periods`: Local return period estimates for fixed wind intensity thresholds
- `exceedance_intensity`: Local wind intensity associated with a specific return period (e.g., 100-year wind)

### Formats
- `csv`: Point-based comma-separated files with location and hazard values
- `nc`: NetCDF format with point-based hazard data
- `raster.nc`: NetCDF raster format on a regular 180 arcsecond grid; use with caution over ocean regions due to coarse interpolation

## Climate Models and Scenarios

| Climate Model         | Reference                         |
|-----------------------|-----------------------------------|
| CESM2                 | Danabasoglu et al. (2020)         |
| CNRM-CM6-1            | Voldoire et al. (2019)            |
| EC-Earth3             | EC-Earth Consortium (2019)        |
| IPSL-CM6A-LR          | Hourdin et al. (2020)             |
| MIROC6                | Tatebe et al. (2019)              |
| UKESM1-0-LL           | Sellar et al. (2020)              |

Scenarios:
- `ssp245`
- `ssp370`
- `ssp585`

Periods:
- `base`: 1995–2014 (historical baseline)
- `fut1`: 2041–2060 (mid-century)
- `fut2`: 2081–2100 (late century)

## Variable Definitions

- `TCGI`: Tropical Cyclone Genesis Index
  - `CRH`: Column-integral relative humidity
  - `SD`: Saturation deficit
- `H08`: Holland 2008 wind field parameterization

## Ensemble Info

- `80ens`: Single-GCM simulation representing 80 ensembles which results in approximately 1600 synthetic years of TCs

Example path:
```
CHAZ_hazard_maps/exceedance_intensity/csv/per-GCM/CESM2/ssp370/TC_global_0300as_CHAZ_CESM2_fut1_ssp370_80ens_CRH_H08_exceedance_intensity.csv
```

## File Naming Convention

All files follow the standardized naming pattern:

```
TC_<basin>_<res>_CHAZ_<GCM>_<period>_<scenario>_<ens>_<TCGI>_<wind>_<map>.<format>
```

For example:

```
TC_global_0300as_CHAZ_CESM2_fut1_ssp370_80ens_CRH_H08_exceedance_intensity.csv
```

With:
- `<basin>`: always `global`
- `<res>`: spatial resolution (`0300as` = 300 arcseconds ≈ 9.3km at the equator)
- `<GCM>`: climate model or `ERA5` or `ALL-MODELS`
- `<period>`: time window (`base`, `fut1`, `fut2`)
- `<scenario>`: climate scenario (`ssp245`, `ssp370`, `ssp585`)
- `<ens>`: number of ensemble years (`80ens`, `480ens`)
- `<TCGI>`: tropical cyclone genesis index moisture formulation (`CRH` or `SD`)
- `<wind>`: wind model used (`H08` = Holland 2008)
- `<map>`: `return_periods` or `exceedance_intensity`
- `<format>`: `csv`, `nc` (NetCDF), or `raster.nc` (gridded NetCDF)

## Usage Notes

- Wind fields are primarily designed for land-based impact assessments. We do not recommend using values over oceans.
- Use caution when comparing different TCGI variants (CRH vs SD).

## Related Resources

- [CHAZ hazard modeling framework (GitHub)](\url{https://github.com/cl3225/CHAZ})
- Associated article: Meiler et al., submitted to Scientific Data

## Licensing and Citation

This dataset is released under the Creative Commons Zero (CC0) waiver. You are free to reuse, modify, and redistribute it. If you use this dataset in your research, please cite the associated publication and credit the authors accordingly.

---

For questions or feedback, please contact: **Simona Meiler**, simona@simonameiler.ch
