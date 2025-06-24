import sys
import argparse
import gc
import rioxarray
import numpy as np
from pathlib import Path
from climada.util.constants import SYSTEM_DIR
from climada.hazard import TropCyclone, Hazard

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from main.hazard_map_utils import gdf_to_netcdf, gdf_to_raster

def main(lon_min, lon_max, lat_min, lat_max, scenario, cat, wind, period):
    assert lon_min < lon_max and lat_min < lat_max, "Invalid spatial extent: check min/max values."

    basin = "global"
    models = ["CESM2", "CNRM-CM6-1", "EC-Earth3", "IPSL-CM6A-LR", "MIROC6", "UKESM1-0-LL"]
    haz_dir = SYSTEM_DIR / "hazard" / "future" / "CHAZ"

    all_events = []
    for model in models:
        file = haz_dir / f"TC_{basin}_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{cat}_{wind}.hdf5"
        print(f"Loading hazard from: {file}")
        tc_hazard = TropCyclone.from_hdf5(file)
        tc_hazard.event_id = np.arange(tc_hazard.intensity.shape[0])
        print(f"Loaded {tc_hazard.size} events.")
        all_events.append(tc_hazard)

    print("Concatenating all hazard sets")
    combined_hazard = Hazard.concat(all_events)
    combined_hazard.event_id = np.arange(combined_hazard.intensity.shape[0])

    print("Selecting regional subset")
    comb_haz_split = combined_hazard.select(extent=(lon_min, lon_max, lat_min, lat_max))

    # Free memory
    del combined_hazard
    gc.collect()

    print("Computing local exceedance intensity...")
    gdf_exceed, _, _ = comb_haz_split.local_exceedance_intensity(
        return_periods=[10, 25, 50, 100, 250, 1000],
        method="extrapolate_constant"
    )

    out_dir = haz_dir / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)

    fname_base = f"TC_{lon_min}_{lon_max}_{lat_min}_{lat_max}_0300as_CHAZ_ALL-MODELS_{period}_{scenario}_480ens_{cat}_{wind}"
    
    description = {
        col: f"Exceedance intensity for RP={col} years"
        for col in gdf_exceed.columns if col != "geometry"
    }

    print("Saving NetCDF map...")
    gdf_to_netcdf(
        gdf_exceed,
        out_dir / f"{fname_base}_exceedance_intensity.nc",
        variable_prefix="rp",
        description=description,
        units="m/s"
    )

    print("Saving gridded raster map...")
    gdf_to_raster(
        gdf_exceed,
        out_dir / f"{fname_base}_exceedance_intensity_raster.nc",
        variable_prefix="rp",
        grid_res=0.05,
        method="linear",
        description=description,
        units="m/s"
    )

    print("Finished processing combined hazard maps.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute combined global hazard exceedance and return period maps.")
    parser.add_argument("--lon_min", type=float, required=True, help="Minimum longitude")
    parser.add_argument("--lon_max", type=float, required=True, help="Maximum longitude")
    parser.add_argument("--lat_min", type=float, required=True, help="Minimum latitude")
    parser.add_argument("--lat_max", type=float, required=True, help="Maximum latitude")
    parser.add_argument("--scenario", type=str, required=True, help="Climate scenario (e.g., ssp370)")
    parser.add_argument("--cat", type=str, required=True, help="Category threshold (e.g., cat1)")
    parser.add_argument("--wind", type=str, required=True, help="Wind field (e.g., vmax)")
    parser.add_argument("--period", type=str, required=True, help="Time period (e.g., 2050)")
    args = parser.parse_args()
    main(**vars(args))
