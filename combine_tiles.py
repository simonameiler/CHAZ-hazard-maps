import sys
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from hazard_map_utils import gdf_to_netcdf, gdf_to_raster

def combine_tiles(input_dir, output_dir, base_name, variable):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern = f"TC_*_*_*_*_{base_name}_{variable}.nc"
    nc_files = sorted(input_dir.glob(pattern))

    if not nc_files:
        print(f"No tile NetCDF files found for pattern: {pattern}")
        return

    print(f"Found {len(nc_files)} tiles for variable '{variable}'. Merging...")

    # Step 1: Load all datasets into GeoDataFrames
    gdfs = []
    for f in nc_files:
        ds = xr.open_dataset(f)
        df = ds.to_dataframe().reset_index()
        gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.lon, df.lat)], crs="EPSG:4326")
        gdfs.append(gdf)

    # Step 2: Combine all GeoDataFrames
    combined_gdf = pd.concat(gdfs, ignore_index=True)
    print(f"Combined GeoDataFrame contains {len(combined_gdf)} points.")

    # Step 3: Define metadata
    if variable == "exceedance_intensity":
        variable_prefix = "rp"
        description = {
            col: f"Exceedance intensity for RP={col[3:]} years"
            for col in combined_gdf.columns if col.startswith("rp_")
        }
        units = "m/s"
    elif variable == "return_periods":
        variable_prefix = "thr"
        description = {
            col: f"Return period for wind speed ≥ {col[4:]} m/s"
            for col in combined_gdf.columns if col.startswith("thr_")
        }
        units = "years"
    else:
        raise ValueError(f"Unknown variable type: {variable}")

    # Step 4: Save original point-based NetCDF and CSV
    nc_out = output_dir / f"TC_global_{base_name}_{variable}.nc"
    gdf_to_netcdf(
        combined_gdf,
        nc_out,
        variable_prefix=variable_prefix,
        description=description,
        units=units,
        also_csv=True
    )

    # Step 5: Save gridded (rasterized) NetCDF
    raster_out = output_dir / f"TC_global_{base_name}_{variable}_raster.nc"
    gdf_to_raster(
        combined_gdf,
        raster_out,
        variable_prefix=variable_prefix,
        grid_res=0.05,
        method="linear",
        description=description,
        units=units
    )

if __name__ == "__main__":
    input_dir = "/cluster/work/climate/meilers/climada/data/hazard/future/CHAZ/maps"
    output_dir = input_dir
    base_name = "0300as_CHAZ_ERA5"
    variable = "exceedance_intensity"  # or "return_periods"

    combine_tiles(input_dir, output_dir, base_name, variable)
