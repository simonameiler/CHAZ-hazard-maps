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
    metric   = "exceedance_intensity"
    rp100_var= "rp_100"
    k         = 5  # nearest neighbors

    # — Cities of interest —
    cities = {
        "Noumea":    {"lon": 166.45,  "lat": -22.28},
        "Miami":     {"lon": -80.2,   "lat": 25.8},
        "Acapulco":  {"lon": -99.9,   "lat": 16.8},
        "Toamasina": {"lon": 49.37,   "lat": -18.15},
        "Mumbai":    {"lon": 72.8,    "lat": 18.9},
        "Manila":    {"lon": 121.0,   "lat": 14.6},
    }

    # — Reference grid & neighbors —
    ds_ref = xr.open_dataset(hazard_dir / f"TC_global_0300as_CHAZ_CESM2_base_ssp245_80ens_{tcgi}_H08_{metric}.nc")
    city_neighbors = find_nearest_indices(ds_ref, cities, k)

    # — All return-period variables (sorted numerically) —
    rp_vars = sorted(
        [v for v in ds_ref.data_vars if v.startswith("rp_")],
        key=lambda v: int(v.split("_")[1])
    )
    rp_years = [int(v.split("_")[1]) for v in rp_vars]

    # — GCMs & scenarios —
    models  = [
        "CESM2", "CNRM-CM6-1", "EC-Earth3",
        "IPSL-CM6A-LR", "MIROC6", "UKESM1-0-LL"
    ]
    periods = ["base", "fut1", "fut2"]
    ssps    = ["ssp245", "ssp370", "ssp585"]

    # — Prepare containers —
    # for rp100: rows100[city][(scenario, stat)] = value
    rows100 = {city: {} for city in cities}
    # for all rp: rows_all[city][(scenario,rp_year,stat)] = value
    rows_all = {city: {} for city in cities}

    # — Loop over scenarios & models —
    for period in periods:
        for ssp in ssps:
            scen = f"{period}_{ssp}_{tcgi}"

            # accumulate per-city lists
            accum100 = {city: [] for city in cities}
            accum_all = {
                rp_year: {city: [] for city in cities}
                for rp_year in rp_years
            }

            for model in models:
                fname = (
                    f"TC_global_0300as_CHAZ_{model}_{period}_"
                    f"{ssp}_80ens_{tcgi}_H08_{metric}.nc"
                )
                ds = xr.open_dataset(hazard_dir / fname)

                # RP-100
                arr100 = ds[rp100_var].values
                for city, idxs in city_neighbors.items():
                    accum100[city].append(round(float(np.nanmean(arr100[idxs])),2))

                # all RP_*
                for v, rp_year in zip(rp_vars, rp_years):
                    arr = ds[v].values
                    for city, idxs in city_neighbors.items():
                        accum_all[rp_year][city].append(
                            round(float(np.nanmean(arr[idxs])),2)
                        )

            # compute min/max for rp100
            for city, vals in accum100.items():
                rows100[city][(scen, "min")] = min(vals)
                rows100[city][(scen, "median")] = float(np.median(vals))
                rows100[city][(scen, "max")] = max(vals)

            # compute min/max for each rp_year
            for rp_year, dic in accum_all.items():
                for city, vals in dic.items():
                    rows_all[city][(scen, rp_year, "min")] = min(vals)
                    rows_all[city][(scen, rp_year, "median")] = float(np.median(vals))
                    rows_all[city][(scen, rp_year, "max")] = max(vals)

    # — Build rp100 DataFrame (MultiIndex columns) —
    df100 = pd.DataFrame.from_dict(rows100, orient="index")
    df100.columns = pd.MultiIndex.from_tuples(
        df100.columns, names=["Scenario", "Statistic"]
    )
    df100 = df100.sort_index(axis=1, level=0)

    # — Build all-RP DataFrame (MultiIndex columns) —
    df_all = pd.DataFrame.from_dict(rows_all, orient="index")
    df_all.columns = pd.MultiIndex.from_tuples(
        df_all.columns, names=["Scenario", "Return Period (yr)", "Statistic"]
    )
    df_all = df_all.sort_index(axis=1, level=[0,1])

    # — Write CSVs —
    out1 = out_dir / f"rp100_gcm_minmaxmed_{tcgi}.csv"
    df100.to_csv(out1)
    print(f"Wrote RP-100 GCM min/max as {out1}")

    out2 = out_dir / f"rp_allperiods_gcm_minmaxmed_{tcgi}.csv"
    df_all.to_csv(out2)
    print(f"Wrote all-RP GCM min/max as {out2}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute per-city RP-100 and all-RP min/max/med across GCMs."
    )
    parser.add_argument("--tcgi",   required=True,
                        help="TCGI choice: CRH or SD")
    parser.add_argument("--out-dir", default="./outputs",
                        help="Directory to write CSVs")
    args = parser.parse_args()
    main(args.tcgi, args.out_dir)
