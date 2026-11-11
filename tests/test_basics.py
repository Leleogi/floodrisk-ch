"""Unit tests that need no network and no heavy geospatial stack beyond numpy/xarray."""

import numpy as np
import pytest

from floodrisk.config import load_aoi


def test_load_aoi():
    aoi = load_aoi("zurich")
    assert aoi.west < aoi.east and aoi.south < aoi.north
    with pytest.raises(KeyError):
        load_aoi("atlantis")


def test_slope_of_plane():
    pytest.importorskip("rasterio")
    from floodrisk.terrain import slope_degrees

    # plane rising 1 m per 1 m cell in x -> 45 degrees
    dem = np.tile(np.arange(10, dtype=float), (10, 1))
    s = slope_degrees(dem, cell_size=1.0)
    assert np.allclose(s[5, 3:7], 45.0, atol=0.5)


def test_deaccumulate():
    xr = pytest.importorskip("xarray")
    from floodrisk.data.era5 import deaccumulate

    acc = xr.DataArray([1.0, 3.0, 3.0, 6.0], dims="valid_time")
    out = deaccumulate(acc)
    assert out.values.tolist() == [1.0, 2.0, 0.0, 3.0]


def test_lv95_tile_range_covers_rotated_wgs84_box():
    from floodrisk.data.swisstopo import lv95_tile_range

    # Zurich pilot box: corners fall in LV95 tiles x 2675..2690, y 1241..1255
    assert lv95_tile_range((8.44, 47.32, 8.63, 47.44)) == (2675, 1241, 2690, 1255)
