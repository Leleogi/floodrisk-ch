"""Rain to runoff with the SCS Curve Number (CN) method.

Idea: not all rain becomes surface runoff. The ground can soak up a certain amount (S, in mm).
Before any runoff starts, the first part of the rain (the "initial abstraction", Ia) is lost to
interception and infiltration. After that, runoff Q grows with the cumulative rain P:

    S  = 25400 / CN - 254            (mm)   potential maximum retention
    Ia = 0.2 * S                     (mm)   initial abstraction (standard assumption)
    Q  = (P - Ia)^2 / (P - Ia + S)   (mm)   if P > Ia, otherwise 0

Everything here works on *cumulative* event rainfall, because the method is defined for the
whole storm so far. Hourly runoff is the difference of cumulative runoff between hours.

The CN values below are generic textbook-style numbers for illustration (hydrologic soil group B,
average antecedent moisture). They are a starting point, not a calibrated Swiss parameter set.
Replacing them with values derived from real Swiss land cover and soil data is a later step.

This module only needs numpy at import time, so the core functions are easy to test.
"""

from __future__ import annotations

import numpy as np

# Generic CN values, soil group B, average wetness (illustrative, to be refined).
CN_TABLE: dict[str, int] = {
    "forest": 60,
    "grassland": 69,
    "cropland": 78,
    "residential": 85,
    "urban_dense": 92,
    "paved": 98,
    "water": 100,
}

DEFAULT_CN = 80  # a middle value used when no land cover is available yet


def retention_s(cn: np.ndarray | float) -> np.ndarray:
    """Potential maximum retention S (mm) from the curve number."""
    cn = np.asarray(cn, dtype="float64")
    if np.any((cn <= 0) | (cn > 100)):
        raise ValueError("CN must be in (0, 100].")
    return 25400.0 / cn - 254.0


def cumulative_runoff_mm(p_cum_mm: np.ndarray, cn: np.ndarray | float, ia_ratio: float = 0.2) -> np.ndarray:
    """Cumulative runoff depth Q (mm) for cumulative rainfall P (mm).

    p_cum_mm and cn broadcast against each other, so cn can be a single number or a
    grid of CN values matching the rain grid.
    """
    p = np.asarray(p_cum_mm, dtype="float64")
    s = retention_s(cn)
    ia = ia_ratio * s
    excess = np.clip(p - ia, 0.0, None)
    denom = excess + s
    # where S == 0 (CN == 100, open water) all rain is runoff: Q = P
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(denom > 0, excess**2 / denom, p)
    return np.where(s == 0, p, q)


def hourly_runoff_mm(p_hourly_mm: np.ndarray, cn: np.ndarray | float, time_axis: int = 0) -> np.ndarray:
    """Hourly runoff (mm) from hourly rainfall (mm) along `time_axis`."""
    p_cum = np.cumsum(np.asarray(p_hourly_mm, dtype="float64"), axis=time_axis)
    q_cum = cumulative_runoff_mm(p_cum, cn)
    q_hourly = np.diff(q_cum, axis=time_axis, prepend=0.0)
    return np.clip(q_hourly, 0.0, None)


def cn_from_landcover(classes: np.ndarray, table: dict[str, int] | None = None) -> np.ndarray:
    """Map an array of land-cover class names to CN values (unknown classes get DEFAULT_CN)."""
    table = table or CN_TABLE
    out = np.full(np.shape(classes), DEFAULT_CN, dtype="float64")
    classes = np.asarray(classes)
    for name, cn in table.items():
        out[classes == name] = cn
    return out


def event_runoff(precip_path, cn: float = DEFAULT_CN):
    """Compute CN runoff for a downloaded ERA5-Land event file.

    Returns an xarray Dataset with hourly precipitation, cumulative precipitation, CN runoff
    (hourly and cumulative, in mm) and, if present in the file, ERA5-Land's own surface runoff
    for comparison.
    """
    import xarray as xr

    from floodrisk.data.era5 import deaccumulate

    ds = xr.open_dataset(precip_path)
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"

    p_hourly = deaccumulate(ds["tp"], time_dim=time_dim) * 1000.0  # m -> mm
    p_cum = p_hourly.cumsum(time_dim)

    q_cum = xr.apply_ufunc(cumulative_runoff_mm, p_cum, cn)
    q_hourly = q_cum.diff(time_dim, label="upper").clip(min=0)
    q_hourly = xr.concat([q_cum.isel({time_dim: slice(0, 1)}), q_hourly], dim=time_dim)

    out = xr.Dataset(
        {
            "precip_hourly_mm": p_hourly,
            "precip_cum_mm": p_cum,
            "runoff_cn_hourly_mm": q_hourly,
            "runoff_cn_cum_mm": q_cum,
        }
    )
    if "sro" in ds:  # ERA5-Land surface runoff, accumulated like precipitation
        sro = deaccumulate(ds["sro"], time_dim=time_dim) * 1000.0
        out["runoff_era5_hourly_mm"] = sro
        out["runoff_era5_cum_mm"] = sro.cumsum(time_dim)
    out.attrs["curve_number"] = float(cn)
    return out
