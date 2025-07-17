#!/usr/bin/env python3
import xarray as xr
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from climada.util.constants import SYSTEM_DIR

def find_nearest_indices(ds_ref, cities, k=5):
    """
    For each city, find the indices of the k nearest grid points
    on the ds_ref (ERA-5) lon/lat arrays.
    """
    lons = ds_ref.lon.values
    lats = ds_ref.lat.values
    city_idxs = {}
    for name, crd in cities.items():
        d2 = (lons - crd["lon"])**2 + (lats - crd["lat"])**2
        city_idxs[name] = np.argsort(d2)[:k]
    return city_idxs

def main(tcgi, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # — Paths & constants —
    hazard_dir = SYSTEM_DIR / "hazard" / "future" / "CHAZ" / "maps"
    metric    = "return_periods"
    vars_thr  = ["thr_33", "thr_50"]
    models    = [
        "CESM2", "CNRM-CM6-1", "EC-Earth3",
        "IPSL-CM6A-LR", "MIROC6", "UKESM1-0-LL"
    ]
    periods   = ["base", "fut1", "fut2"]
    ssps      = ["ssp245", "ssp370", "ssp585"]
    k         = 5  # nearest neighbours

    # — Cities of interest —
    cities = {
        "Noumea":    {"lon": 166.45,  "lat": -22.28},
        "Miami":     {"lon": -80.2,   "lat": 25.8},
        "Acapulco":  {"lon": -99.9,   "lat": 16.8},
        "Toamasina": {"lon": 49.37,   "lat": -18.15},
        "Mumbai":    {"lon": 72.8,    "lat": 18.9},
        "Manila":    {"lon": 121.0,   "lat": 14.6},
    }

    # — Reference grid for buffering —
    ds_ref = xr.open_dataset(hazard_dir / f"TC_global_0300as_CHAZ_CESM2_base_ssp245_80ens_{tcgi}_H08_{metric}.nc")
    city_neighbors = find_nearest_indices(ds_ref, cities, k=k)

    # — Prepare accumulator: rows[city][(scenario, var, stat)] = value
    rows = {c: {} for c in cities}

    # — Loop over scenarios & models —
    for period in periods:
        for ssp in ssps:
            scen = f"{period}_{ssp}_{tcgi}"

            # scratch space for each city & variable
            accum = {
                var: {c: [] for c in cities}
                for var in vars_thr
            }

            for model in models:
                fname = (
                    f"TC_global_0300as_CHAZ_{model}_{period}_"
                    f"{ssp}_80ens_{tcgi}_H08_{metric}.nc"
                )
                ds = xr.open_dataset(hazard_dir / fname)

                # for each threshold variable
                for var in vars_thr:
                    arr = ds[var].values
                    for city, idxs in city_neighbors.items():
                        accum[var][city].append(round(float(np.nanmean(arr[idxs])),2))

            # once all models done, compute min/median/max
            for var in vars_thr:
                for city, vals in accum[var].items():
                    rows[city][(scen, var, "min")]    = min(vals)
                    rows[city][(scen, var, "median")] = float(np.median(vals))
                    rows[city][(scen, var, "max")]    = max(vals)

    # — Build DataFrame with MultiIndex columns —
    df = pd.DataFrame.from_dict(rows, orient="index")
    df.columns = pd.MultiIndex.from_tuples(
        df.columns, names=["Scenario", "Threshold", "Statistic"]
    )
    # sort by scenario, then threshold, then statistic
    df = df.sort_index(axis=1, level=[0,1,2])

    # — Save CSV —
    out_file = out_dir / f"thresholds_gcm_minmaxmed_{tcgi}.csv"
    df.to_csv(out_file)
    print(f"Wrote threshold GCM min/max/med table as {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute per-city thr_33 & thr_50 min/max across GCMs."
    )
    parser.add_argument("--tcgi",   required=True,
                        help="Choose TCGI: CRH or SD")
    parser.add_argument("--out-dir", default="./outputs",
                        help="Directory to write CSV")
    args = parser.parse_args()
    main(args.tcgi, args.out_dir)
