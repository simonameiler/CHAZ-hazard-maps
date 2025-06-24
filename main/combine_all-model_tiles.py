import sys
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

sys.path.append("/cluster/project/climate/meilers/scripts/columbia_haz_maps")
from hazard_map_utils import gdf_to_raster

def gdf_to_clean_netcdf(gdf, path, description, units):
    """
    Save a GeoDataFrame to a NetCDF file with clean variable names: lat, lon, and data columns only.
    """
    df = pd.DataFrame(gdf.drop(columns='geometry'))
    ds = xr.Dataset()

    ds.coords['lat'] = ('points', df['lat'].values)
    ds.coords['lon'] = ('points', df['lon'].values)

    for col in df.columns:
        if col in ['lat', 'lon']:
            continue
        ds[col] = (('points',), df[col].values)
        ds[col].attrs['description'] = description.get(col, "")
        ds[col].attrs['units'] = units

    ds.to_netcdf(path)
    print(f"Saved clean NetCDF to {path}")


def combine_tiles(input_dir, output_dir, base_pattern, variable):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern = f"TC_*_*_*_*_{base_pattern}_{variable}.nc"
    nc_files = sorted(input_dir.glob(pattern))

    if not nc_files:
        print(f"No tile NetCDF files found for pattern: {pattern}")
        return

    print(f"🔍 Found {len(nc_files)} tiles for '{base_pattern}' / variable '{variable}'. Merging...")

    gdfs = []
    for f in nc_files:
        ds = xr.open_dataset(f)
        df = ds.to_dataframe().reset_index()
        df = df.dropna(subset=['lat', 'lon'])
        gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.lon, df.lat)], crs="EPSG:4326")
        gdfs.append(gdf)

    combined_gdf = pd.concat(gdfs, ignore_index=True)
    combined_gdf = combined_gdf.drop_duplicates(subset=["lat", "lon"])  # safety
    print(f"Combined GeoDataFrame has {len(combined_gdf)} points.")

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
        raise ValueError(f"Unknown variable: {variable}")

    # Clean NetCDF
    out_name = f"TC_global_{base_pattern}_{variable}"
    gdf_to_clean_netcdf(
        combined_gdf,
        output_dir / f"{out_name}.nc",
        description=description,
        units=units
    )

    # Gridded (rasterized) NetCDF
    gdf_to_raster(
        combined_gdf,
        output_dir / f"{out_name}_raster.nc",
        variable_prefix=prefix,
        grid_res=0.05,
        method="linear",
        description=description,
        units=units
    )

    print(f"Finished: {out_name}.nc and {out_name}_raster.nc")


if __name__ == "__main__":
    input_dir = "/cluster/work/climate/meilers/climada/data/hazard/future/CHAZ/maps"
    output_dir = input_dir

    scenarios = ["ssp245", "ssp370", "ssp585"]
    periods = ["base", "fut1", "fut2"]
    cat = "CRH"
    wind = "H08"

    variable = "return_periods"  # or "exceedance_intensity"

    for scenario in scenarios:
        for period in periods:
            base_pattern = f"0300as_CHAZ_ALL-MODELS_{period}_{scenario}_480ens_{cat}_{wind}"
            combine_tiles(input_dir, output_dir, base_pattern, variable)
