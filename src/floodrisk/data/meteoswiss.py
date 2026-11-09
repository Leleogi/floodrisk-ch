"""MeteoSwiss ICON-CH1/CH2-EPS forecast access via the swisstopo/FSDI STAC API.

Phase 3 of the plan. For now this only lists available forecast files so you can explore
the structure; decoding GRIB2 on the native icosahedral grid is added later.

Docs: https://opendatadocs.meteoswiss.ch/general/download
Demos: https://github.com/MeteoSwiss/opendata-nwp-demos
"""

from __future__ import annotations

import requests

STAC_SEARCH = "https://data.geo.admin.ch/api/stac/v1/search"
COLLECTIONS = {
    "ch1": "ch.meteoschweiz.ogd-forecasting-icon-ch1",  # 1 km, 11 members, 33 h
    "ch2": "ch.meteoschweiz.ogd-forecasting-icon-ch2",  # 2.1 km, 21 members, 120 h
}


def list_forecast_items(model: str = "ch2", limit: int = 10) -> list[dict]:
    """Return the most recent STAC items of an ICON collection (metadata only)."""
    body = {"collections": [COLLECTIONS[model]], "limit": limit}
    resp = requests.post(STAC_SEARCH, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json().get("features", [])
