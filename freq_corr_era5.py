
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script for CHAZ hazard frequency correction and basin-wise processing.
"""

import os
import re
import numpy as np
from pathlib import Path
from shapely.geometry import Polygon, Point

from climada.hazard import Centroids, TropCyclone
from climada.util.constants import SYSTEM_DIR
from climada.util.coordinates import lon_normalize

# Define EP–NA boundary
EP_NA_BOUNDARY_LINE = [
    (-100.0, 60.0),
    (-100.0, 18.0),
    (-90.0, 18.0),
    (-90.0, 15.0),
    (-85.0, 15.0),
    (-85.0, 9.0),
    (-75.0, 9.0),
    (-75.0, 5.0)
]

# Define constants
YRLY_FREQ_IB_LIT = {
    'EP': 14.5, 'NA': 10.8, 'NI': 2.0,
    'SI': 12.3, 'SP': 9.3, 'WP': 22.5
}

BASIN_BOUNDARIES = {
    'EP': Polygon([(-180, 60), (-180, 5)] + EP_NA_BOUNDARY_LINE[::-1]),
    'NA': Polygon(EP_NA_BOUNDARY_LINE + [(0, 5), (0, 60)]),
    'NI': (30.0, 100.0, 5.0, 60.0),
    'SI': (10.0, 135.0, -60.0, -5.0),
    'SP': (135.0, -120.0, -60.0, -5.0),
    'WP': (100.0, 180.0, 5.0, 60.0)
}

REGION_ID = {
    'EP': 6000, 'NA': 6001, 'NI': 6002,
    'SI': 6003, 'SP': 6004, 'WP': 6005
}


def is_polygon(basin_geom):
    return isinstance(basin_geom, Polygon)


def basin_split_haz(hazard, basin):
    """Split global TropCyclone hazard into basin using polygons or bounding boxes."""
    geom = BASIN_BOUNDARIES[basin]
    region_id = REGION_ID[basin]

    if is_polygon(geom):
        basin_idx = np.array([
            geom.contains(Point(lon, lat)) for lat, lon in hazard.centroids.coord
        ])
    else:
        lonmin, lonmax, latmin, latmax = geom
        if lonmax < lonmin:
            basin_idx = (
                (hazard.centroids.lat > latmin) &
                (hazard.centroids.lat < latmax) &
                ((hazard.centroids.lon > lonmin) | (hazard.centroids.lon < lonmax))
            )
        else:
            basin_idx = (
                (hazard.centroids.lat > latmin) &
                (hazard.centroids.lat < latmax) &
                (hazard.centroids.lon > lonmin) &
                (hazard.centroids.lon < lonmax)
            )

    hazard.centroids.region_id[basin_idx] = region_id
    return hazard.select(reg_id=region_id)


def split_and_correct_basins(hazard):
    """Split hazard by basin, apply frequency correction."""
    basin_hazards = {}

    for bsn in BASIN_BOUNDARIES:
        tc_haz_basin = basin_split_haz(hazard, bsn)
        num_tracks = tc_haz_basin.intensity.max(axis=1).getnnz()
        observed_freq = YRLY_FREQ_IB_LIT[bsn]
        simulated_freq = num_tracks / 15600
        base_freq = (observed_freq / simulated_freq) / 15600
        tc_haz_basin.frequency = np.full(tc_haz_basin.size, base_freq)
        basin_hazards[bsn] = tc_haz_basin

    return basin_hazards


def rename_events_per_basin(hazards_dict):
    """Assign clean, unique names and dates to each event per basin."""
    basin_offsets = {
        'EP': 0,
        'NA': 100000,
        'NI': 200000,
        'SI': 300000,
        'SP': 400000,
        'WP': 500000
    }

    for basin, hazard in hazards_dict.items():
        n_ev = len(hazard.event_id)
        offset = basin_offsets[basin]
        hazard.event_id = np.array([f"ev{i}_{basin}" for i in range(n_ev)])
        hazard.event_name = [f"ev{i}_{basin}" for i in range(n_ev)]
        hazard.event_date = np.arange(offset, offset + n_ev)


def save_basin_and_global_hazards(hazards_dict, haz_out):
    """Save each basin hazard and concatenate into a global hazard object."""
    for bsn, hazard in hazards_dict.items():
        out_file = haz_out / f"TC_{bsn}_0300as_CHAZ_ERA5_freq-corr.hdf5"
        hazard.write_hdf5(out_file)

    rename_events_per_basin(hazards_dict)
    global_haz = TropCyclone.concat(list(hazards_dict.values()))
    global_file = haz_out / f"TC_global_0300as_CHAZ_ERA5_freq-corr.hdf5"
    global_haz.write_hdf5(global_file)


if __name__ == "__main__":
    haz_dir = Path("/nfs/n2o/wcr/meilers/data/hazard/present")
    file = "TC_global_0300as_CHAZ_ERA5.hdf5"
    chaz_base = TropCyclone.from_hdf5(haz_dir / file)
    base_hazards = split_and_correct_basins(chaz_base)
    save_basin_and_global_hazards(base_hazards, haz_dir)
