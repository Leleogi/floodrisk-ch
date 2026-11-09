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
