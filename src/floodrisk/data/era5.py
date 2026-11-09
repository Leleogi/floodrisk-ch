"""ERA5-Land hourly download via the Copernicus Climate Data Store (CDS) API.

Setup (one-off): create a free account at https://cds.climate.copernicus.eu, copy your
personal access token from your profile page, put it in ~/.cdsapirc:

    url: https://cds.climate.copernicus.eu/api
    key: <your-personal-access-token>

and accept the licence on the dataset page:
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

Resolution is about 9 km, so local convective cells are smoothed out. Use it for large-scale
events and as a first demo; add radar/station data later for validation.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import xarray as xr

from floodrisk.config import AOI, DATA_RAW

DATASET = "reanalysis-era5-land"
VARIABLES = [
    "total_precipitation",
    "surface_runoff",
    "sub_surface_runoff",
    "volumetric_soil_water_layer_1",
]


def download_event(aoi: AOI, day: date, out_dir: Path | None = None, pad_deg: float = 0.1) -> Path:
    """Download one day (24 hourly steps) of ERA5-Land for the AOI (plus a small padding)."""
    import cdsapi  # imported lazily so the package works without CDS credentials

    out_dir = out_dir or (DATA_RAW / "era5land" / aoi.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"era5land_{day.isoformat()}.nc"
    if target.exists():
        return target

    request = {
        "variable": VARIABLES,
        "year": f"{day.year:04d}",
        "month": f"{day.month:02d}",
        "day": f"{day.day:02d}",
        "time": [f"{h:02d}:00" for h in range(24)],
        # CDS area order: North, West, South, East
        "area": [aoi.north + pad_deg, aoi.west - pad_deg, aoi.south - pad_deg, aoi.east + pad_deg],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client = cdsapi.Client()
    client.retrieve(DATASET, request).download(str(target))
    return target


def deaccumulate(da: xr.DataArray, time_dim: str = "valid_time") -> xr.DataArray:
    """Turn ERA5-Land accumulated fields into per-hour values.

    ERA5-Land accumulations run from 00 UTC of each day: the value at hour h is the sum from
    00:00 up to h. So hourly amount = value(h) - value(h-1), and the first step of the day
    is taken as is. Assumes the data covers whole days in chronological order.
    """
    diff = da.diff(time_dim, label="upper")
    first = da.isel({time_dim: slice(0, 1)})
    out = xr.concat([first, diff], dim=time_dim)
    # negative values can appear at the day boundary or from rounding: clip them
    return out.clip(min=0)


def event_precip_mm(path: Path) -> xr.DataArray:
    """Hourly precipitation in mm for a downloaded event file."""
    ds = xr.open_dataset(path)
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"
    tp = deaccumulate(ds["tp"], time_dim=time_dim) * 1000.0  # m -> mm
    tp.attrs["units"] = "mm"
    return tp


def max_intensity_mm_per_h(precip_mm: xr.DataArray) -> float:
    """Peak hourly area-mean precipitation, a quick event summary."""
    spatial = [d for d in precip_mm.dims if d in ("latitude", "longitude")]
    return float(np.nanmax(precip_mm.mean(spatial).values))
