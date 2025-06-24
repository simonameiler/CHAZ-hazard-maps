import sys
import gc
import rioxarray
import argparse
import numpy as np
from pathlib import Path
from climada.hazard import TropCyclone

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from main.hazard_map_utils import gdf_to_netcdf, gdf_to_raster

def main(lon_min, lon_max, lat_min, lat_max):
    basin = "global"
    haz_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/")
    file = haz_dir / f"TC_{basin}_0300as_CHAZ_ERA5_freq-corr.hdf5"

    print(f"Loading hazard from: {file}")
    tc_hazard = TropCyclone.from_hdf5(file)
    tc_hazard.event_id = np.arange(tc_hazard.intensity.shape[0])

    # Select the region based on input bounds
    hazard_split = tc_hazard.select(extent=(lon_min, lon_max, lat_min, lat_max))
    
    # delete the original hazard object to free up memory
    del tc_hazard
    gc.collect()

    gdf_return, _, _ = hazard_split.local_return_period(
        threshold_intensities=[33, 50], method="extrapolate_constant"
    )

    out_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/future/CHAZ/maps")
    out_dir.mkdir(parents=True, exist_ok=True)

    fname_base = f"TC_{lon_min}_{lon_max}_{lat_min}_{lat_max}_0300as_CHAZ_ERA5"

    gdf_to_netcdf(
        gdf_return,
        out_dir / f"{fname_base}_return_periods.nc",
        variable_prefix="thr",
        description={
            col: f"Return period for intensity ≥ {col} m/s"
            for col in gdf_return.columns if col != "geometry"
        },
        units="years"
    )

    gdf_to_raster(
        gdf_return,
        out_dir / f"{fname_base}_return_periods_raster.nc",
        variable_prefix="thr",
        grid_res=0.05,
        method="linear",
        description={
            col: f"Return period for intensity ≥ {col} m/s"
            for col in gdf_return.columns if col != "geometry"
        },
        units="years"
    )

    print(f"Finished processing {file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lon_min", type=float, required=True, help="Minimum longitude")
    parser.add_argument("--lon_max", type=float, required=True, help="Maximum longitude")
    parser.add_argument("--lat_min", type=float, required=True, help="Minimum latitude")
    parser.add_argument("--lat_max", type=float, required=True, help="Maximum latitude")
    args = parser.parse_args()

    main(args.lon_min, args.lon_max, args.lat_min, args.lat_max)
