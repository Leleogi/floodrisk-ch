# floodrisk-ch

Event-driven flood (surface runoff) risk mapping for Switzerland, built only on open data.

**Idea:** feed in a rain event (MeteoSwiss ICON forecast or an ERA5-Land hindcast) and get a
hazard map plus a building-level risk estimate.

```
Risk = Hazard (where does water go?) x Exposure (which buildings?) x Vulnerability (how badly hurt?)
```

Status: **early development.** Phase 1 (terrain + data download) and the first part of phase 2
(Curve Number runoff) are implemented. Runoff functions are unit-tested; the data download and
terrain steps have not yet been run end-to-end. See `docs/PLAN.md` for the roadmap.

## Pilot area

Start with the **City of Zurich** (about 92 km2, 2 m terrain model, roughly 23 M cells, fine for
a MacBook M2). Fallback: **Canton Zug**. Both are defined in `config/aoi.yml`.

## Quick start

```bash
# 1. environment (conda/mamba recommended for geospatial libs on Apple Silicon)
mamba env create -f environment.yml
conda activate floodrisk

# 2. install the package in editable mode
pip install -e .

# 3. download the 2 m terrain model for the pilot area
floodrisk dem --aoi zurich

# 4. derive terrain indicators (slope, flow accumulation, HAND)
floodrisk terrain --aoi zurich

# 5. download ERA5-Land for an event (needs a free CDS account, see docs/DATA_SOURCES.md)
floodrisk era5 --aoi zurich --date 2021-07-13

# 6. turn that event into Curve Number runoff (saves a NetCDF and a comparison plot)
floodrisk runoff --aoi zurich --date 2021-07-13 --cn 80
```

New to the topic? Read `docs/CONCEPTS.md` for a plain-language walkthrough of the model.

## Layout

```
config/aoi.yml          areas of interest (WGS84 bounding boxes)
src/floodrisk/
  config.py             paths and AOI loading
  data/swisstopo.py     swissALTI3D download via the swisstopo STAC API
  data/era5.py          ERA5-Land download via the Copernicus CDS API
  data/meteoswiss.py    ICON-CH1/CH2-EPS forecast item listing (STAC)
  terrain.py            slope, flow accumulation, HAND
  runoff.py             SCS Curve Number: rain to surface runoff
  plots.py              event rain/runoff figure
  cli.py                `floodrisk` command line
docs/CONCEPTS.md        how the model works, in plain language
docs/PLAN.md            phases and milestones
docs/DATA_SOURCES.md    data sources, licences, caveats
tests/                  small unit tests (no network needed)
data/                   raw / interim / processed (git-ignored)
```

## Data and licences

All data used is open government or Copernicus data. Attribution is required, for example
"Federal Office of Topography swisstopo". Details in `docs/DATA_SOURCES.md`.

## Disclaimer

Research and demo project. Not a replacement for official hazard maps (cantonal
Gefahrenkarten, BAFU Gefaehrdungskarte Oberflaechenabfluss) and not suitable for planning or
insurance decisions.
