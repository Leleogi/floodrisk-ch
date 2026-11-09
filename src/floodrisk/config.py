"""Paths and area-of-interest (AOI) loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# repo root = two levels above src/floodrisk
ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
AOI_FILE = ROOT / "config" / "aoi.yml"


@dataclass(frozen=True)
class AOI:
    name: str
    description: str
    bbox: tuple[float, float, float, float]  # west, south, east, north (WGS84)
    dem_resolution_m: float

    @property
    def west(self) -> float:
        return self.bbox[0]

    @property
    def south(self) -> float:
        return self.bbox[1]

    @property
    def east(self) -> float:
        return self.bbox[2]

    @property
    def north(self) -> float:
        return self.bbox[3]


def load_aoi(name: str) -> AOI:
    with open(AOI_FILE, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if name not in cfg:
        raise KeyError(f"Unknown AOI '{name}'. Available: {', '.join(cfg)}")
    entry = cfg[name]
    return AOI(
        name=name,
        description=entry.get("description", ""),
        bbox=tuple(entry["bbox"]),
        dem_resolution_m=float(entry.get("dem_resolution_m", 2)),
    )
