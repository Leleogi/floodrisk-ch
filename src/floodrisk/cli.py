"""Command line interface: `floodrisk dem|terrain|era5|icon`."""

from __future__ import annotations

import argparse
from datetime import date

from floodrisk.config import load_aoi


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="floodrisk", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dem = sub.add_parser("dem", help="download swissALTI3D tiles for an AOI")
    p_dem.add_argument("--aoi", default="zurich")

    p_ter = sub.add_parser("terrain", help="compute slope, flow accumulation and HAND")
    p_ter.add_argument("--aoi", default="zurich")
    p_ter.add_argument("--stream-threshold", type=int, default=5000)

    p_era = sub.add_parser("era5", help="download one ERA5-Land day for an AOI")
    p_era.add_argument("--aoi", default="zurich")
    p_era.add_argument("--date", required=True, help="YYYY-MM-DD")

    sub.add_parser("icon", help="list the latest ICON-CH2-EPS items (exploration only)")

    args = parser.parse_args(argv)

    if args.cmd == "dem":
        from floodrisk.data.swisstopo import download_dem

        paths = download_dem(load_aoi(args.aoi))
        print(f"Done: {len(paths)} tiles")
    elif args.cmd == "terrain":
        from floodrisk.terrain import compute_indicators

        out = compute_indicators(load_aoi(args.aoi), stream_threshold_cells=args.stream_threshold)
        for name, path in out.items():
            print(f"{name}: {path}")
    elif args.cmd == "era5":
        from floodrisk.data.era5 import download_event

        path = download_event(load_aoi(args.aoi), date.fromisoformat(args.date))
        print(f"Saved {path}")
    elif args.cmd == "icon":
        from floodrisk.data.meteoswiss import list_forecast_items

        for item in list_forecast_items("ch2"):
            print(item["id"])


if __name__ == "__main__":
    main()
