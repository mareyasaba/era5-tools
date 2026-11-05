#!/bin/bash -e
# Build GRTCODE ERA5 input files for a range of years.
#   ./run_download.sh 2022 2025
# Runs in the background and logs to logs/era5_<start>-<end>_<timestamp>.log.
cd "$(dirname "$(readlink -f "$0")")"
start=${1:?usage: $0 start_year [end_year]}
end=${2:-$start}

source ./env.sh

# Pre-flight checks, so problems show up now and not after a long CDS wait.
command -v cdo >/dev/null     || { echo "ERROR: cdo not found (module load cdo/2.3.0-omp)"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
[ -f ~/.cdsapirc ]            || { echo "ERROR: ~/.cdsapirc missing (CDS API key)"; exit 1; }
python3 -c "import cdsapi, xarray, netCDF4, scipy, numpy" \
    || { echo "ERROR: missing python packages: pip install --user cdsapi xarray netCDF4 scipy"; exit 1; }
python3 -c "import era5" 2>/dev/null \
    || { echo "ERROR: era5 package not installed: pip install --user -e ."; exit 1; }

mkdir -p logs data monthly
log="logs/era5_${start}-${end}_$(date +%Y%m%d-%H%M%S).log"
{
  echo "git commit: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "cdo:        $(cdo --version 2>&1 | head -1)"
  echo "python:     $(python3 --version)"
} > "$log"
nohup python3 -u download_2021to2025.py --start "$start" --end "$end" >> "$log" 2>&1 &
echo "Started (pid $!). Follow with: tail -f $log"
