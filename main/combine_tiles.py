import sys
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from main.hazard_map_utils import gdf_to_raster


def gdf_to_clean_netcdf(gdf, path, description, units, also_csv=False):
    """
    Save a GeoDataFrame to a NetCDF file with clean lat/lon and variable names.
    """
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    ds = xr.Dataset()

    ds.coords["lat"] = ("points", df["lat"].values)
    ds.coords["lon"] = ("points", df["lon"].values)

    for col in df.columns:
        if col in ["lat", "lon"]:
            continue
        ds[col] = ("points", df[col].values)
        ds[col].attrs["description"] = description.get(col, "")
        ds[col].attrs["units"] = units

    ds.to_netcdf(path)
    print(f"Saved clean NetCDF to: {path}")

    if also_csv:
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"Also saved CSV to: {csv_path}")


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

    gdfs = []
    for f in nc_files:
        ds = xr.open_dataset(f)
        df = ds.to_dataframe().reset_index()
        df = df.dropna(subset=["lat", "lon"])
        gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.lon, df.lat)], crs="EPSG:4326")
        gdfs.append(gdf)

    combined_gdf = pd.concat(gdfs, ignore_index=True)
    combined_gdf = combined_gdf.drop_duplicates(subset=["lat", "lon"])
    print(f"Combined GeoDataFrame contains {len(combined_gdf)} points.")

    # Define metadata
    if variable == "exceedance_intensity":
        prefix = "rp"
        description = {
            col: f"Exceedance intensity for RP={col[3:]} years"
            for col in combined_gdf.columns if col.startswith("rp_")
        }
        units = "m/s"
    elif variable == "return_periods":
        prefix = "thr"
        description = {
            col: f"Return period for wind speed ≥ {col[4:]} m/s"
            for col in combined_gdf.columns if col.startswith("thr_")
        }
        units = "years"
    else:
        raise ValueError(f"Unknown variable type: {variable}")

    base_out = f"TC_global_{base_name}_{variable}"
    nc_out = output_dir / f"{base_out}.nc"
    raster_out = output_dir / f"{base_out}_raster.nc"

    # Save clean point-based NetCDF and CSV
    gdf_to_clean_netcdf(
        combined_gdf,
        nc_out,
        description=description,
        units=units,
        also_csv=True
    )

    # Save gridded raster NetCDF
    gdf_to_raster(
        combined_gdf,
        raster_out,
        variable_prefix=prefix,
        grid_res=0.05,
        method="linear",
        description=description,
        units=units
    )

    print(f"Finished combining tiles for: {base_out}")


if __name__ == "__main__":
    input_dir = "/cluster/work/climate/meilers/climada/data/hazard/future/CHAZ/maps"
    output_dir = input_dir
    base_name = "0300as_CHAZ_ERA5"
    variable = "exceedance_intensity"  # or "return_periods"

    combine_tiles(input_dir, output_dir, base_name, variable)
