"""Terrain indicators from swissALTI3D tiles: slope, flow accumulation, HAND.

Flow routing uses pysheds. HAND (Height Above Nearest Drainage) is a good, cheap proxy for
"how low-lying is this cell relative to the nearest stream" and is a standard flood indicator.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge

from floodrisk.config import AOI, DATA_INTERIM, DATA_PROCESSED, DATA_RAW

# pysheds 0.5 still calls np.in1d, which numpy 2.4 removed (np.isin is the replacement).
if not hasattr(np, "in1d"):
    np.in1d = np.isin


def mosaic_tiles(aoi: AOI) -> Path:
    """Merge downloaded DEM tiles into one GeoTIFF (EPSG:2056)."""
    tile_dir = DATA_RAW / "swissalti3d" / aoi.name
    tiles = sorted(tile_dir.glob("*.tif"))
    if not tiles:
        raise FileNotFoundError(f"No tiles in {tile_dir}. Run `floodrisk dem --aoi {aoi.name}` first.")
    out = DATA_INTERIM / f"dem_{aoi.name}.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    srcs = [rasterio.open(p) for p in tiles]
    try:
        mosaic, transform = merge(srcs)
        meta = srcs[0].meta.copy()
        meta.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=transform,
            compress="deflate",
        )
        with rasterio.open(out, "w", **meta) as dst:
            dst.write(mosaic)
    finally:
        for s in srcs:
            s.close()
    return out


def slope_degrees(dem: np.ndarray, cell_size: float) -> np.ndarray:
    """Slope in degrees from a DEM array (central differences)."""
    dz_dy, dz_dx = np.gradient(dem.astype("float64"), cell_size)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def compute_indicators(aoi: AOI, stream_threshold_cells: int = 5000) -> dict[str, Path]:
    """Compute slope, flow accumulation and HAND, and write them as GeoTIFFs.

    stream_threshold_cells: cells draining into a cell before it counts as a stream.
    With 2 m cells, 5000 cells is about 0.02 km2. Tune this; it is the main HAND knob.
    """
    from pysheds.grid import Grid  # imported lazily: heavy dependency

    dem_path = mosaic_tiles(aoi)
    out_dir = DATA_PROCESSED / aoi.name
    out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(dem_path) as src:
        profile = src.profile.copy()
        cell = abs(src.transform.a)
        dem_arr = src.read(1)
        nodata = src.nodata

    profile.update(dtype="float32", count=1, compress="deflate", nodata=-9999.0)
    results: dict[str, Path] = {}

    def _write(name: str, arr: np.ndarray) -> Path:
        path = out_dir / f"{name}_{aoi.name}.tif"
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(np.where(np.isfinite(arr), arr, -9999.0).astype("float32"), 1)
        results[name] = path
        return path

    dem_f = dem_arr.astype("float64")
    nodata_mask = (dem_arr == nodata) if nodata is not None else np.zeros(dem_arr.shape, bool)
    dem_f[nodata_mask] = np.nan

    slope = slope_degrees(np.nan_to_num(dem_f, nan=np.nanmean(dem_f)), cell)
    slope[nodata_mask] = np.nan
    _write("slope", slope)

    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))
    filled = grid.fill_pits(dem)
    filled = grid.fill_depressions(filled)
    inflated = grid.resolve_flats(filled)
    fdir = grid.flowdir(inflated)
    acc = grid.accumulation(fdir)
    acc_arr = np.asarray(acc, dtype="float64")
    acc_arr[nodata_mask] = np.nan
    _write("flowacc", acc_arr)

    streams = acc > stream_threshold_cells
    hand = np.asarray(grid.compute_hand(fdir, inflated, streams), dtype="float64")
    # Cells whose flow path leaves the DEM into a nodata gap get measured against the nodata
    # value (-9999) and end up with HAND in the thousands of metres. A real HAND can never
    # exceed the cell's height above the lowest valid DEM cell, so mask anything above that.
    hand[nodata_mask | (hand > dem_f - np.nanmin(dem_f))] = np.nan
    _write("hand", hand)
    return results
