import sys
import argparse
import numpy as np
from pathlib import Path
from climada.hazard import TropCyclone

def test_split(lat_min, lat_max, lon_min, lon_max):
    basin = "global"
    haz_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/")
    file = haz_dir / f"TC_{basin}_0300as_CHAZ_ERA5_freq-corr.hdf5"

    print(f"Loading hazard from: {file}")
    tc_hazard = TropCyclone.from_hdf5(file)
    tc_hazard.event_id = np.arange(tc_hazard.intensity.shape[0])

    # Split
    hazard_split = tc_hazard.select(extent=(lon_min, lat_min, lon_max, lat_max))

    print(f"Bounding box: ({lat_min}, {lat_max}) / ({lon_min}, {lon_max})")
    print(f"Selected {hazard_split.intensity.size} intensity values "
          f"with shape {hazard_split.intensity.shape}")
    print(f"Number of events: {len(hazard_split.event_id)}")
    print(f"Number of grid points: {hazard_split.centroids.size}")
    print("Sample lat/lon points:")
    for i, centroid in enumerate(hazard_split.centroids.coord[:5]):
        print(f"  Point {i+1}: lat = {centroid[1]:.2f}, lon = {centroid[0]:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat_min", type=float, required=True, help="Minimum latitude")
    parser.add_argument("--lat_max", type=float, required=True, help="Maximum latitude")
    parser.add_argument("--lon_min", type=float, required=True, help="Minimum longitude")
    parser.add_argument("--lon_max", type=float, required=True, help="Maximum longitude")
    args = parser.parse_args()

    test_split(args.lat_min, args.lat_max, args.lon_min, args.lon_max)