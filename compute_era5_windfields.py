#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute CHAZ windfields from track simulations using Holland (2008) wind model.
"""

import sys
import copy
import numpy as np
from pathlib import Path
from pathos.pools import ProcessPool as Pool
from climada.hazard import Centroids, TCTracks, TropCyclone
from climada.util.constants import SYSTEM_DIR

def main(i_file):
    i_file = int(i_file)  # Ensemble index: 0..9

    # Paths and filenames
    chaz_dir = Path("/nfs/n2o/wcr/meilers/data/tracks/CHAZ/ERA-5")
    haz_dir = SYSTEM_DIR / "hazard" / "present"
    haz_dir.mkdir(parents=True, exist_ok=True)

    fname = chaz_dir / f"global_2019_2ens00{i_file}_pre.nc"
    cent_file = SYSTEM_DIR / "earth_centroids_0300as_global.hdf5"

    # Load CHAZ tracks (no year filtering for ERA5)
    tracks = TCTracks.from_simulations_chaz(fname)

    # Load relevant centroids
    cent = Centroids.from_hdf5(cent_file)
    cent_tracks = cent.select(extent=tracks.get_extent(5))

    # Compute windfields in chunks
    k = 1000
    for n in range(0, tracks.size, k):
        tracks_chunk = copy.deepcopy(tracks)
        tracks_chunk.data = tracks.data[n:n+k]
        tracks_chunk.equal_timestep(time_step_h=.5)
        tc = TropCyclone.from_tracks(tracks_chunk, centroids=cent_tracks, model='H08')
        out_name = f"TC_global_0300as_CHAZ_ERA5_2ens00{i_file}_H08_{n}.hdf5"
        tc.write_hdf5(haz_dir / out_name)

if __name__ == "__main__":
    main(*sys.argv[1:])
