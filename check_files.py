from pathlib import Path
from itertools import product

# --- Config (without MPI-ESM1-2-HR) ---
models = [
    "CESM2", "CNRM-CM6-1", "EC-Earth3", "IPSL-CM6A-LR",
    "MIROC6", "UKESM1-0-LL"
]
periods = ["base", "fut1", "fut2"]
scenarios = ["ssp245", "ssp370", "ssp585"]
tcgis = ["CRH", "SD"]
vars_ = ["exceedance_intensity", "return_periods"]
extensions = [".nc", ".csv", "_raster.nc"]

# --- Folder path ---
from climada.util.constants import SYSTEM_DIR
haz_dir = SYSTEM_DIR / "hazard" / "future" / "CHAZ_update" / "maps"

# --- Get all existing files in the folder ---
all_files = {f.name for f in haz_dir.glob("*")}

# --- Loop over extensions ---
for ext in extensions:
    expected_files = {
        f"TC_global_0300as_CHAZ_{model}_{period}_{scenario}_80ens_{tcgi}_H08_{var}{ext}"
        for model, period, scenario, tcgi, var in product(models, periods, scenarios, tcgis, vars_)
    }
    
    found_files = expected_files & all_files
    missing_files = sorted(expected_files - all_files)

    # --- Report ---
    print(f"\n=== Checking extension: {ext} ===")
    print(f"Expected files: {len(expected_files)}")
    print(f"Found files:    {len(found_files)}")
    print(f"Missing files:  {len(missing_files)}\n")

    for fname in missing_files:
        print(fname)
