"""Download swissALTI3D elevation tiles for an AOI via the swisstopo STAC API.

STAC collection: ch.swisstopo.swissalti3d
Docs: https://www.swisstopo.admin.ch/en/height-model-swissalti3d
Attribution required: "Federal Office of Topography swisstopo".
"""

from __future__ import annotations

import re
from pathlib import Path

import requests

from floodrisk.config import AOI, DATA_RAW

STAC_ROOT = "https://data.geo.admin.ch/api/stac/v1"
COLLECTION = "ch.swisstopo.swissalti3d"


def lv95_tile_range(bbox_wgs84: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    """1 km LV95 tile index range (x_min, y_min, x_max, y_max, inclusive) covering a WGS84 bbox.

    A WGS84 box is slightly rotated against the LV95 grid, so tiles that only touch its
    LV95 envelope are not returned by a plain STAC bbox query. Using the full envelope keeps
    the DEM mosaic a complete rectangle without nodata corners.
    """
    from pyproj import Transformer

    w, s, e, n = bbox_wgs84
    t = Transformer.from_crs(4326, 2056, always_xy=True)
    xs, ys = t.transform([w, e, w, e], [s, s, n, n])
    return (
        int(min(xs) // 1000),
        int(min(ys) // 1000),
        int(max(xs) // 1000),
        int(max(ys) // 1000),
    )


def _query_bbox(aoi: AOI) -> tuple[float, float, float, float]:
    """WGS84 bbox enclosing the full LV95 tile range of the AOI (for the STAC query)."""
    from pyproj import Transformer

    x0, y0, x1, y1 = lv95_tile_range(aoi.bbox)
    t = Transformer.from_crs(2056, 4326, always_xy=True)
    lons, lats = t.transform(
        [x0 * 1000, (x1 + 1) * 1000, x0 * 1000, (x1 + 1) * 1000],
        [y0 * 1000, y0 * 1000, (y1 + 1) * 1000, (y1 + 1) * 1000],
    )
    return min(lons), min(lats), max(lons), max(lats)


def _iter_items(aoi: AOI):
    """Yield all STAC items intersecting the AOI's LV95 tile envelope (follows pagination)."""
    url = f"{STAC_ROOT}/collections/{COLLECTION}/items"
    params = {"bbox": ",".join(f"{v:.6f}" for v in _query_bbox(aoi)), "limit": 100}
    while url:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        yield from payload.get("features", [])
        url = next(
            (link["href"] for link in payload.get("links", []) if link.get("rel") == "next"),
            None,
        )
        params = None  # the "next" link already carries the query


def _pick_asset(item: dict, resolution_m: float) -> dict | None:
    """Pick the GeoTIFF asset matching the requested ground sampling distance."""
    for asset in item.get("assets", {}).values():
        href = asset.get("href", "")
        if not href.endswith(".tif"):
            continue
        gsd = asset.get("eo:gsd")
        if gsd is not None and float(gsd) == float(resolution_m):
            return asset
        # fallback: swisstopo file names contain e.g. "..._2_2056_5728.tif" (2 m) or "_0.5_"
        res_token = f"_{resolution_m:g}_2056"
        if res_token in href:
            return asset
    return None


def _tile_key(item_id: str) -> str:
    """Tile key without year, e.g. 'swissalti3d_2019_2683-1248' -> '2683-1248'."""
    m = re.search(r"(\d{4}-\d{4})$", item_id)
    return m.group(1) if m else item_id


def list_tiles(aoi: AOI) -> list[dict]:
    """Return one asset per tile (latest year wins) for the AOI."""
    x0, y0, x1, y1 = lv95_tile_range(aoi.bbox)
    best: dict[str, tuple[str, dict]] = {}
    for item in _iter_items(aoi):
        asset = _pick_asset(item, aoi.dem_resolution_m)
        if asset is None:
            continue
        key = _tile_key(item["id"])
        # the query bbox is a little larger than the tile envelope; drop tiles outside it
        m = re.fullmatch(r"(\d{4})-(\d{4})", key)
        if m and not (x0 <= int(m.group(1)) <= x1 and y0 <= int(m.group(2)) <= y1):
            continue
        if key not in best or item["id"] > best[key][0]:
            best[key] = (item["id"], asset)
    return [asset for _, asset in best.values()]


def download_dem(aoi: AOI, out_dir: Path | None = None) -> list[Path]:
    """Download all DEM tiles for the AOI into data/raw/swissalti3d/<aoi>/ (skips existing)."""
    out_dir = out_dir or (DATA_RAW / "swissalti3d" / aoi.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    assets = list_tiles(aoi)
    if not assets:
        raise RuntimeError("No swissALTI3D tiles found for this AOI/resolution.")
    print(f"{len(assets)} tiles to fetch for '{aoi.name}' at {aoi.dem_resolution_m:g} m")
    paths: list[Path] = []
    for i, asset in enumerate(assets, 1):
        href = asset["href"]
        target = out_dir / href.rsplit("/", 1)[-1]
        paths.append(target)
        if target.exists():
            continue
        with requests.get(href, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        if i % 10 == 0 or i == len(assets):
            print(f"  {i}/{len(assets)}")
    return paths
