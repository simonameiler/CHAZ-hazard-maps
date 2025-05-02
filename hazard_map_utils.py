# hazard_map_utils.py
import os
import xarray as xr
import rioxarray
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from scipy.interpolate import griddata

from climada.util.constants import SYSTEM_DIR

def df_to_raster(
    df,
    out_path,
    variable_prefix='hazard_metric',
    grid_res=0.05,
    method='linear',
    description=None,
    units=None,
):
    """
    Interpolate hazard metric data from a DataFrame with lat/lon to a regular grid and save as NetCDF.
    """
    lon = df["lon"].values
    lat = df["lat"].values

    lon_min, lon_max = np.floor(lon.min()), np.ceil(lon.max())
    lat_min, lat_max = np.floor(lat.min()), np.ceil(lat.max())
    lon_grid = np.arange(lon_min, lon_max + grid_res, grid_res)
    lat_grid = np.arange(lat_min, lat_max + grid_res, grid_res)
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

    coords = {"lon": lon_grid, "lat": lat_grid}
    interpolated_vars = {}

    numeric_cols = df.select_dtypes(include=["number"]).columns.difference(["lat", "lon"])

    for col in numeric_cols:
        values = df[col].values
        grid_values = griddata((lon, lat), values, (lon_mesh, lat_mesh), method=method)

        var_name = f"{variable_prefix}_{col}".replace(".", "p")
        da = xr.DataArray(grid_values, dims=("lat", "lon"), coords=coords)

        if description and col in description:
            da.attrs["long_name"] = description[col] if isinstance(description, dict) else description
        if units and (isinstance(units, dict) and col in units or isinstance(units, str)):
            da.attrs["units"] = units[col] if isinstance(units, dict) else units

        interpolated_vars[var_name] = da

    ds = xr.Dataset(interpolated_vars)
    ds.to_netcdf(out_path)
    print(f"Saved rasterized NetCDF to: {out_path}")

def gdf_to_raster(
    gdf,
    out_path,
    variable_prefix='hazard_metric',
    grid_res=0.05,
    method='linear',
    description=None,
    units=None,
):
    """
    Interpolate hazard metric data from a GeoDataFrame onto a regular grid and save as NetCDF.
    No cropping to land; this step should be done separately.
    """
    lon = gdf.geometry.x.values
    lat = gdf.geometry.y.values

    lon_min, lon_max = np.floor(lon.min()), np.ceil(lon.max())
    lat_min, lat_max = np.floor(lat.min()), np.ceil(lat.max())
    lon_grid = np.arange(lon_min, lon_max + grid_res, grid_res)
    lat_grid = np.arange(lat_min, lat_max + grid_res, grid_res)
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

    coords = {"lon": lon_grid, "lat": lat_grid}
    interpolated_vars = {}

    numeric_cols = gdf.select_dtypes(include=['number']).columns

    for col in numeric_cols:
        values = gdf[col].values
        grid_values = griddata((lon, lat), values, (lon_mesh, lat_mesh), method=method)

        var_name = f"{variable_prefix}_{col}".replace(".", "p")
        da = xr.DataArray(grid_values, dims=("lat", "lon"), coords=coords)

        if description and col in description:
            da.attrs['long_name'] = description[col] if isinstance(description, dict) else description

        if units and (isinstance(units, dict) and col in units or isinstance(units, str)):
            da.attrs['units'] = units[col] if isinstance(units, dict) else units

        interpolated_vars[var_name] = da

    ds = xr.Dataset(interpolated_vars)
    ds.to_netcdf(out_path)
    print(f"Saved gridded raster NetCDF to {out_path}")
    
def gdf_to_netcdf(gdf, out_path, variable_prefix='hazard_metric', description=None, units=None, also_csv=True):
    """
    Save GeoDataFrame with hazard metrics as NetCDF (and optionally CSV).
    """
    ds = xr.Dataset()
    ds.coords['lon'] = ('points', gdf.geometry.x)
    ds.coords['lat'] = ('points', gdf.geometry.y)

    for col in gdf.columns:
        if col == 'geometry':
            continue

        var_name = f"{variable_prefix}_{col}".replace(".", "p")
        data_array = xr.DataArray(gdf[col].values, dims=("points",))

        # Add optional metadata, only if the key exists
        if description:
            if isinstance(description, dict) and col in description:
                data_array.attrs['long_name'] = description[col]
            elif isinstance(description, str):
                data_array.attrs['long_name'] = description

        if units:
            if isinstance(units, dict) and col in units:
                data_array.attrs['units'] = units[col]
            elif isinstance(units, str):
                data_array.attrs['units'] = units

        ds[var_name] = data_array

    ds.to_netcdf(out_path)
    print(f"Saved NetCDF to {out_path}")

    if also_csv:
        csv_path = str(out_path).replace(".nc", ".csv")
        gdf_csv = gdf.copy()
        gdf_csv["lon"] = gdf_csv.geometry.x
        gdf_csv["lat"] = gdf_csv.geometry.y
        gdf_csv = gdf_csv.drop(columns="geometry")
        cols = ["lon", "lat"] + [col for col in gdf_csv.columns if col not in ["lon", "lat"]]
        gdf_csv[cols].to_csv(csv_path, index=False)
        print(f"Saved CSV to {csv_path}")

# def gdf_to_netcdf(gdf, out_path, variable_prefix='hazard_metric', description=None, units=None, also_csv=True):
#     """
#     Save GeoDataFrame with hazard metrics as NetCDF (and optionally CSV).

#     Parameters
#     ----------
#     gdf : gpd.GeoDataFrame
#         GeoDataFrame with geometry and metric columns.
#     out_path : Path or str
#         Path to NetCDF file to be saved.
#     variable_prefix : str, optional
#         Prefix to use for unnamed variables. Defaults to 'hazard_metric'.
#     description : str or dict, optional
#         Optional description for each variable (str if common to all, dict if per column).
#     units : str or dict, optional
#         Optional units for each variable (str if common to all, dict if per column).
#     also_csv : bool, optional
#         If True, also export as CSV with same name. Defaults to True.
#     """
#     ds = xr.Dataset()
#     ds.coords['lon'] = ('points', gdf.geometry.x)
#     ds.coords['lat'] = ('points', gdf.geometry.y)

#     for i, col in enumerate(gdf.columns):
#         if col == 'geometry':
#             continue
#         var_name = f"{variable_prefix}_{col}".replace(".", "p")
#         data_array = xr.DataArray(gdf[col].values, dims=("points",))

#         # Add optional metadata
#         if description:
#             desc = description[col] if isinstance(description, dict) else description
#             data_array.attrs['long_name'] = desc
#         if units:
#             unit = units[col] if isinstance(units, dict) else units
#             data_array.attrs['units'] = unit

#         ds[var_name] = data_array

#     # Assign CRS
#     #ds.rio.write_crs(gdf.crs, inplace=True)
#     ds.to_netcdf(out_path)
#     print(f"Saved NetCDF to {out_path}")

#     if also_csv:
#         csv_path = str(out_path).replace(".nc", ".csv")

#         # Add lon and lat as separate columns
#         gdf_csv = gdf.copy()
#         gdf_csv["lon"] = gdf_csv.geometry.x
#         gdf_csv["lat"] = gdf_csv.geometry.y
#         gdf_csv = gdf_csv.drop(columns="geometry")

#         # Save with lon/lat as the first columns
#         cols = ["lon", "lat"] + [col for col in gdf_csv.columns if col not in ["lon", "lat"]]
#         gdf_csv[cols].to_csv(csv_path, index=False)
#         print(f"Saved CSV to {csv_path}")


def crop_netcdf_to_land(input_nc, output_nc, shapefile_path, buffer_dist=0.0):
    """
    Crop a rasterized NetCDF file to land-only points using a Natural Earth shapefile.

    Parameters:
    -----------
    input_nc : str
        Path to the input NetCDF file.
    output_nc : str
        Path to the output cropped NetCDF file.
    shapefile_path : str
        Path to the Natural Earth land shapefile (e.g., ne_10m_land.shp).
    buffer_dist : float
        Buffer distance in degrees to optionally extend land polygons.
    """
    
    ds = xr.open_dataset(input_nc)
    ds = ds.rio.write_crs("EPSG:4326", inplace=True)
    ds.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)

    land_gdf = gpd.read_file(shapefile_path).to_crs("EPSG:4326")
    if buffer_dist != 0:
        land_gdf["geometry"] = land_gdf.geometry.buffer(buffer_dist)

    ds_clipped = ds.rio.clip(land_gdf.geometry, land_gdf.crs, drop=True)

    if "spatial_ref" in ds_clipped.coords:
        ds_clipped = ds_clipped.drop_vars("spatial_ref")

    ds_clipped.to_netcdf(output_nc)
    print(f"Successfully saved land-cropped NetCDF to {output_nc}")
