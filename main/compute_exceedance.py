import sys
import argparse
import rioxarray
import numpy as np
from pathlib import Path
from climada.util.constants import SYSTEM_DIR
from climada.hazard import TropCyclone

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from main.hazard_map_utils import gdf_to_netcdf, gdf_to_raster

def main(model, scenario, cat, wind, period):
    basin = "global"
    #haz_dir = Path("/nfs/n2o/wcr/meilers/data/hazard/future/CHAZ-update")
    haz_dir = SYSTEM_DIR/"hazard"/"future"/"CHAZ"
    file = haz_dir / f"TC_{basin}_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{cat}_{wind}.hdf5"

    print(f"Loading hazard from: {file}")
    tc_hazard = TropCyclone.from_hdf5(file)
    tc_hazard.event_id = np.arange(tc_hazard.intensity.shape[0])

    gdf_exceed, _, _ = tc_hazard.local_exceedance_intensity(
        return_periods=[10, 25, 50, 100, 250, 1000], method="extrapolate_constant"
    )

    out_dir = haz_dir / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)

    fname_base = f"TC_{basin}_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{cat}_{wind}"

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

    print(f"Finished exceedance intensity processing for {file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute global hazard exceedance intensity.")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--scenario", type=str, required=True)
    parser.add_argument("--cat", type=str, required=True)
    parser.add_argument("--wind", type=str, required=True)
    parser.add_argument("--period", type=str, required=True)

    args = parser.parse_args()
    main(**vars(args))
