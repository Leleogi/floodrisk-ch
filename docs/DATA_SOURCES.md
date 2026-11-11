# Data sources

| Data | Source | Access | Notes |
|------|--------|--------|-------|
| Terrain (bare earth) | swissALTI3D, swisstopo | https://www.swisstopo.admin.ch/en/height-model-swissalti3d, STAC `ch.swisstopo.swissalti3d` | 0.5 m and 2 m, open, attribution required |
| Surface runoff hazard (baseline) | BAFU Gefaehrdungskarte Oberflaechenabfluss | https://data.geo.admin.ch/browser/index.html#/collections/ch.bafu.gefaehrdungskarte-oberflaechenabfluss | Rare to very rare events, informative only, not legally binding |
| Forecast | MeteoSwiss ICON-CH1/CH2-EPS | https://opendatadocs.meteoswiss.ch/general/download, STAC `ch.meteoschweiz.ogd-forecasting-icon-ch1/ch2` | GRIB2, native icosahedral grid |
| Radar precipitation | MeteoSwiss open data | https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html | Good for validation |
| Reanalysis | ERA5-Land, Copernicus CDS | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land | About 9 km, hourly, free account and licence acceptance |
| Buildings | swissBUILDINGS3D 3.0 Beta, swisstopo | https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0-beta | EGID included for some cantons (check ZH, ZG coverage) |
| Building register | GWR, BFS | via map.geo.admin.ch / BFS | Access terms vary; check |
| Past events | StorMe, BAFU | https://www.bafu.admin.ch/de/naturgefahren-geodaten | For validation |

Always check licence and attribution requirements before publishing results.

## Hydrological Atlas of Switzerland (hydromaps.ch)

**hydromaps.ch shuts down at the end of 2026** (federal budget cuts). Only some maps move to the
Atlas of Switzerland. The copies below were downloaded on 2026-11-11 into `data/raw/hydromaps/`
(git-ignored, about 250 MB) and **cannot be downloaded again from hydromaps.ch after 2026**.
Source: Hydrologischer Atlas der Schweiz (HADES), Uni Bern / BAFU. GeoServer: `https://gs.hydromaps.ch/geoserver`.

| Folder | Content | Format | Use in this project |
|--------|---------|--------|---------------------|
| `a02_catchments/` | A02 catchment boundaries for water balance studies (`a0201_bilanzv1_0`) | zipped shapefile | AOI catchments, check flow accumulation |
| `a04_catchment_properties/` | A04 land cover (~100 m, CH-wide), geology (100 m, CH-wide), land cover "plus" (~15 m, EPSG:3857, clipped to Zurich and Zug + ~5 km buffer) | GeoTIFF | Curve Number inputs (phase 2) |
| `a05_discharge_stations/` | A05 discharge gauging stations and outlets (BAFU and cantonal) | GeoJSON | Validation against measured discharge (phase 3) |
| `b04_extreme_precipitation/` | B04 v3 extreme point precipitation, ~1 km grid, all of CH | GeoPackage, EPSG:4326 | Design storms (phase 2) |
| `f02_human_impact/` | F02 human impact on discharge, ~4,500 catchment outlets | GeoJSON | Context |

**B04 columns:** `b04_<duration>_<return period>a_<quantile>`, values in mm. Durations: `02m 05m 10m 60m 03h 06h 12h 24h 48h 72h`.
Return periods: `002 005 010 020 030 050 100 200 300` years. Quantiles: `0_025` / `0_5` / `0_975`
(lower bound, median, upper bound of the 95 % interval). Example: `b04_60m_100a_0_5` = median 100-year
1-hour rainfall. `f_*` columns are decimal versions for the short durations. The underlying data is
MeteoSwiss's extreme value analysis, which stays online at MeteoSwiss.

**Land cover "plus" classes:** 1 sealed, 2 needle-leaved trees, 3 broadleaved deciduous trees,
4 broadleaved evergreen trees, 5 low-growing woody, 6 permanent herbaceous, 7 periodically herbaceous,
8 lichens and mosses, 9 non or sparsely vegetated, 10 water.

Not downloaded: A04 elevation, slope and aspect (duplicates of swissALTI3D), and the CH-wide
~15 m land cover (about 9.5 GB uncompressed; the server refuses a single request, fetch other AOIs by subset).
