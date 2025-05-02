import sys
import argparse
import rioxarray
import numpy as np
from pathlib import Path
from climada.util.constants import SYSTEM_DIR
from climada.hazard import TropCyclone

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from hazard_map_utils import gdf_to_netcdf, gdf_to_raster

def main(model, scenario, cat, wind, period):
    basin = "global"
    #haz_dir = Path("/nfs/n2o/wcr/meilers/data/hazard/future/CHAZ-update")
    haz_dir = SYSTEM_DIR/"hazard"/"future"/"CHAZ"
    file = haz_dir / f"TC_{basin}_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{cat}_{wind}.hdf5"

    print(f"Loading hazard from: {file}")
    tc_hazard = TropCyclone.from_hdf5(file)
    tc_hazard.event_id = list(range(tc_hazard.intensity.shape[0]))

    gdf_return, _, _ = tc_hazard.local_return_period(
        threshold_intensities=[33, 50], method="extrapolate_constant"
    )

    out_dir = haz_dir / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)

    fname_base = f"TC_{basin}_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{cat}_{wind}"

    gdf_to_netcdf(
        gdf_return,
        out_dir / f"{fname_base}_return_periods.nc",
        variable_prefix="thr",
        description={
            col: f"Return period for intensity \u2265 {col} m/s"
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
            col: f"Return period for intensity \u2265 {col} m/s"
            for col in gdf_return.columns if col != "geometry"
        },
        units="years"
    )

    print(f"Finished return period processing for {file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute global hazard return periods.")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--scenario", type=str, required=True)
    parser.add_argument("--cat", type=str, required=True)
    parser.add_argument("--wind", type=str, required=True)
    parser.add_argument("--period", type=str, required=True)

    args = parser.parse_args()
    main(**vars(args))
