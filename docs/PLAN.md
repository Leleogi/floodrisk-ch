# Project plan

Goal: a demo for the City of Zurich (fallback: Zug) where a rain event goes in and a
hazard + building risk map comes out.

| Phase | Weeks | Deliverable | Done when |
|-------|-------|-------------|-----------|
| 1. Terrain | 1-2 | DEM mosaic, slope, flow accumulation, HAND for the AOI | GeoTIFFs open in QGIS and look plausible; compared to the BAFU Oberflaechenabfluss layer |
| 2. Rain to runoff | 3-4 | ERA5-Land event to effective runoff (SCS Curve Number from soil and land cover) | One known event reproduced; runoff map per hour |
| 3. Routing and depth | 4-5 | Simple depth proxy from runoff and terrain, plus ICON forecast ingest | Validated against StorMe events and BAFU map |
| 4. Buildings | 5-6 | Buildings (swissBUILDINGS3D / GWR via EGID) joined to hazard, simple depth-damage curve | Building table with depth and damage index |
| 5. Demo | 6 | Web map (MapLibre or Streamlit) with event selector | 10-minute walkthrough runs on a laptop |

## Open questions

- Basement information is probably not available nationwide as open data. Start with proxies
  (building age, type, terrain position) and label them clearly.
- ERA5-Land (9 km) misses local thunderstorms. Add radar precipitation products for validation.
- Soil/land cover layers for the Curve Number still to be chosen.

## Later

Scale to canton level or all of Switzerland (tile-based processing), ensemble forecasts
(ICON-CH1/CH2-EPS members to probabilities), uncertainty communication.
