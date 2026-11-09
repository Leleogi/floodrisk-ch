"""Command line interface: `floodrisk dem|terrain|era5|runoff|icon`."""

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

    p_run = sub.add_parser("runoff", help="turn a downloaded ERA5 event into Curve Number runoff")
    p_run.add_argument("--aoi", default="zurich")
    p_run.add_argument("--date", required=True, help="YYYY-MM-DD (same day you downloaded)")
    p_run.add_argument("--cn", type=float, default=80.0, help="Curve Number, 30-100 (default 80)")

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
    elif args.cmd == "runoff":
        from floodrisk.config import DATA_PROCESSED, DATA_RAW
        from floodrisk.plots import plot_event_runoff
        from floodrisk.runoff import event_runoff

        aoi = load_aoi(args.aoi)
        src = DATA_RAW / "era5land" / aoi.name / f"era5land_{args.date}.nc"
        if not src.exists():
            raise SystemExit(f"{src} not found. Run: floodrisk era5 --aoi {aoi.name} --date {args.date}")
        ds = event_runoff(src, cn=args.cn)
        out_dir = DATA_PROCESSED / aoi.name
        out_dir.mkdir(parents=True, exist_ok=True)
        nc_path = out_dir / f"runoff_{args.date}_cn{args.cn:g}.nc"
        ds.to_netcdf(nc_path)
        png_path = plot_event_runoff(
            ds, out_dir / f"runoff_{args.date}_cn{args.cn:g}.png", title=f"{aoi.name}, {args.date}"
        )
        total_p = float(ds["precip_cum_mm"].isel({d: -1 for d in ds["precip_cum_mm"].dims if d.endswith("time")}).mean())
        total_q = float(ds["runoff_cn_cum_mm"].isel({d: -1 for d in ds["runoff_cn_cum_mm"].dims if d.endswith("time")}).mean())
        print(f"Area-mean rain {total_p:.1f} mm -> CN runoff {total_q:.1f} mm")
        print(f"Saved {nc_path}\nSaved {png_path}")
    elif args.cmd == "icon":
        from floodrisk.data.meteoswiss import list_forecast_items

        for item in list_forecast_items("ch2"):
            print(item["id"])


if __name__ == "__main__":
    main()
