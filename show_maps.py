import xarray as xr
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from shapely.geometry import Point

from climada.util.constants import SYSTEM_DIR


# --- CONFIGURABLE SETTINGS ---
netcdf_path = "TC_global_0300as_CHAZ_CESM2_base_SSP245_80ens_CRH_H08_return_periods.nc"
threshold_to_plot = 'thr_33'  # m/s threshold
region_bounds = {
    "Caribbean": [-100, -40, 0, 40],
    "Southeast Asia": [90, 150, 5, 30],
    "Global": [-180, 180, -90, 90]
}
selected_region = "Caribbean"
# -----------------------------

# --- LOAD DATA ---
haz_dir = SYSTEM_DIR/"hazard"/"future"/"CHAZ_update"/"maps"
ds = xr.open_dataset(haz_dir.joinpath(netcdf_path))

# Inspect available thresholds
#print("Available thresholds:", ds["threshold"].values)

# Extract coordinates and return period values
lat = ds["lat"].values
lon = ds["lon"].values
values = ds["thr_33"].values

# --- CREATE GEODATAFRAME ---
df = pd.DataFrame({
    "lat": lat,
    "lon": lon,
    "value": values
})
df["geometry"] = [Point(xy) for xy in zip(df.lon, df.lat)]
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

# --- FILTER TO REGION ---
min_lon, max_lon, min_lat, max_lat = region_bounds[selected_region]
gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]

# --- PLOT ---
fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': ccrs.PlateCarree()})
gdf.plot(column="value", cmap="viridis", markersize=10, ax=ax, legend=True)
ax.set_extent([min_lon, max_lon, min_lat, max_lat])
ax.coastlines()
ax.set_title(f"{threshold_to_plot} m/s Return Period ({selected_region})")
plt.show()
