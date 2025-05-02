from climada.hazard import TropCyclone
from pathlib import Path
from scipy.sparse import csr_matrix
import numpy as np

# --- Set file path ---
basin = "global"
haz_dir = Path("/cluster/work/climate/meilers/climada/data/hazard/")
file_name = haz_dir / f"TC_{basin}_0300as_CHAZ_ERA5_freq-corr.hdf5"

print(f"Loading: {file_name}")
tc = TropCyclone.from_hdf5(file_name)

# --- Extract intensity matrix ---
intens = tc.intensity.tocsr()
n_rows = intens.shape[0]

# --- Containers for cleaned data ---
data_clean = []
indices_clean = []
indptr_clean = [0]  # start with 0

# --- Clean row by row ---
for i in range(n_rows):
    row_start = intens.indptr[i]
    row_end = intens.indptr[i+1]

    row_indices = intens.indices[row_start:row_end]
    row_data = intens.data[row_start:row_end]

    valid_mask = row_indices >= 0

    data_clean.extend(row_data[valid_mask])
    indices_clean.extend(row_indices[valid_mask])
    indptr_clean.append(indptr_clean[-1] + np.sum(valid_mask))

# --- Rebuild cleaned intensity matrix ---
intensity_clean = csr_matrix(
    (np.array(data_clean), np.array(indices_clean), np.array(indptr_clean)),
    shape=intens.shape
)

tc.intensity = intensity_clean

# Final safety check
assert np.all(tc.intensity.indices >= 0), "⚠️ Still has invalid indices!"

# --- Save cleaned file ---
cleaned_file = file_name.with_name(file_name.stem + "_CLEANED.hdf5")
tc.write_hdf5(cleaned_file)
print(f"\n✅ Cleaned hazard saved to: {cleaned_file}")
