from climada.hazard import TropCyclone
from pathlib import Path
import numpy as np

# --- Set file path ---
basin = "global"
haz_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/")
file_name = haz_dir / f"TC_{basin}_0300as_CHAZ_ERA5_freq-corr.hdf5"

print(f"Loading: {file_name}")
tc_haz = TropCyclone.from_hdf5(file_name)

# --- Step 1: Check for negative indices ---
neg_idx = tc_haz.intensity.indices < 0
print(f"\n[Before] Any negative indices? {np.any(neg_idx)}")

# --- Step 2: Try to canonicalize and clean ---
tc_haz.intensity.sum_duplicates()
tc_haz.intensity.eliminate_zeros()

# --- Step 3: Check again ---
neg_idx = tc_haz.intensity.indices < 0
if np.any(neg_idx):
    bad_positions = np.where(neg_idx)[0]
    print(f"\n[After] Still has {len(bad_positions)} bad indices!")
    print("Bad indices:", tc_haz.intensity.indices[bad_positions][:10], "...")
    print("Corresponding data values:", tc_haz.intensity.data[bad_positions][:10], "...")
else:
    print("\n[After] ✅ No negative indices found after cleaning.")

    # --- Optional: Save the cleaned file ---
    cleaned_file = file_name.with_name(file_name.stem + "_CLEANED.hdf5")
    tc_haz.write_hdf5(cleaned_file)
    print(f"\n✅ Cleaned file saved to: {cleaned_file}")
