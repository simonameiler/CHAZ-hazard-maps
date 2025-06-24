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

    gdf_exceed, _, _ = hazard_split.local_exceedance_intensity(
        return_periods=[10, 25, 50, 100, 250, 1000], method="extrapolate_constant"
    )

    out_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/future/CHAZ/maps")
    out_dir.mkdir(parents=True, exist_ok=True)

    fname_base = f"TC_{lon_min}_{lon_max}_{lat_min}_{lat_max}_0300as_CHAZ_ERA5"

    gdf_to_netcdf(
        gdf_exceed,
        out_dir / f"{fname_base}_exceedance_intensity.nc",
        variable_prefix="rp",
        description={
            col: f"Exceedance intensity for RP={col} years"
            for col in gdf_exceed.columns if col != "geometry"
        },
        units="m/s"
    )

    gdf_to_raster(
        gdf_exceed,
        out_dir / f"{fname_base}_exceedance_intensity_raster.nc",
        variable_prefix="rp",
        grid_res=0.05,
        method="linear",
        description={
            col: f"Exceedance intensity for RP={col} years"
            for col in gdf_exceed.columns if col != "geometry"
        },
        units="m/s"
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
