"""Build GRTCODE ERA5 input files ({year}-era5.nc) for a range of years.

Usage:  python3 build_era5_inputs.py --start 2022 --end 2025
(normally run via ./run_download.sh, which loads the modules and checks the setup first)
"""
import argparse
from era5.download import download
from era5.horizontal_remap import remap as hori_remap
from era5.vertical_remap import remap as ver_remap
from era5.remove_negatives import remove_negatives
from pathlib import Path
import os
import xarray as xr

parser = argparse.ArgumentParser(description="Build GRTCODE ERA5 input files.")
parser.add_argument("--start", type=int, default=2022, help="first year (inclusive)")
parser.add_argument("--end", type=int, default=2025, help="last year (inclusive)")
args = parser.parse_args()


os.makedirs("data", exist_ok=True)
os.makedirs("monthly", exist_ok=True)

for year in range(args.start, args.end + 1):   # Jan to Dec of each year
    level_file = Path(f"./data/{year}-level_data.nc")
    single_file = Path(f"./data/{year}-single_data.nc")
    level_file_remap = Path(f"./data/{year}-level_data_remap.nc")
    single_file_remap = Path(f"./data/{year}-single_data_remap.nc")
    output = f"./monthly/{year}-era5.nc"
    # Download if files don't exist
    if not level_file.exists() or not single_file.exists():
        print(f"Downloading data for {year}...")
        download(level_file, single_file, year, year, 1, 12)
    else:
        print(f"Download skipped for {year}, files already exist.")

    # Horizontal remap if remapped files don't exist
    if not level_file_remap.exists():
        print(f"Remapping level file for {year}...")
        hori_remap(level_file, level_file_remap, 144, 90)
        remove_negatives(level_file_remap)
    else:
        print(f"Level remap skipped for {year}.")

    if not single_file_remap.exists():
        print(f"Remapping single file for {year}...")
        hori_remap(single_file, single_file_remap, 144, 90)
        remove_negatives(single_file_remap)
    else:
        print(f"Single remap skipped for {year}.")

    ver_remap(level_file_remap, single_file_remap, f"./data/{year}-level_data_sigma.nc")
    ds1 = xr.open_dataset(f"./data/{year}-level_data_sigma.nc")
    ds2 = xr.open_dataset(single_file_remap)
    combined = xr.merge([ds1, ds2])
    if 'valid_time' in combined.dims:
        combined = combined.rename({'valid_time': 'time'})

    combined.to_netcdf(output)

