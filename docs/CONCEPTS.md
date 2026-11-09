# How the model works, in plain language

This page explains what each part of the project does and why. Read it top to bottom once and the
code layout will make sense.

## The big picture

```
Rain event --> how much becomes surface water? --> where does that water flow? --> which buildings are hit, and how badly?
 (ERA5 / ICON)        (runoff, Curve Number)            (terrain: slope, flow, HAND)         (exposure + vulnerability)
```

Risk is usually written as **Hazard x Exposure x Vulnerability**:

- **Hazard**: how much water, how deep, how fast, at a given place.
- **Exposure**: what is there (buildings, people, roads).
- **Vulnerability**: how much damage a given water depth causes (a basement is far more vulnerable
  than a raised ground floor).

## Step by step

### 1. Terrain (`floodrisk dem`, `floodrisk terrain`)

Water flows downhill, so everything starts with the shape of the land.

- **DEM** (digital elevation model): a grid of heights. We use swissALTI3D, 2 m cells.
- **Slope**: how steep each cell is. Steep slopes shed water fast; flat areas let it pool.
- **Flow accumulation**: for every cell, how many cells drain into it. High values trace valleys and
  streams. This is how the model "knows" where water collects.
- **HAND** (Height Above Nearest Drainage): how many metres a cell sits above the closest stream.
  Cells with a low HAND value flood first. It is a cheap, well-known flood indicator.

### 2. Rain data (`floodrisk era5`)

ERA5-Land is a reanalysis: a weather model constrained by observations, giving hourly values on a
roughly 9 km grid back to 1950. We download rain, ERA5's own surface runoff and soil water for one
day. The values come as running totals since 00:00 UTC, so the code first turns them into
per-hour amounts (`deaccumulate`).

Limit: 9 km cells smooth out short, intense thunderstorms. Good for a first demo, not the final word.

### 3. Rain to runoff (`floodrisk runoff`)

Not all rain runs off. The **SCS Curve Number** method estimates the share that does:

- Each surface gets a Curve Number (CN): about 60 for forest, 98 for pavement.
- CN gives the ground's remaining capacity to soak up water (S).
- The first 20% of S is lost before any runoff begins (the initial abstraction).
- After that, runoff grows with cumulative rain.

Worked example, CN 80 and 100 mm of rain: S = 63.5 mm, the first 12.7 mm soaks in, and
`(100 - 12.7)^2 / (100 - 12.7 + 63.5)` = about 50.5 mm becomes runoff, roughly half.

The command saves the numbers and a plot comparing our runoff estimate with ERA5-Land's own
surface-runoff output. They should be in the same ballpark, not identical: different method,
different grid, different assumptions about soil.

### Coming next

- Route runoff over the terrain (runoff-weighted flow accumulation) to get a water-depth proxy.
- Compare with the official BAFU surface-runoff map and with past events (StorMe).
- Join buildings and apply a depth-damage curve.

## Honest limitations

- CN values are generic, not calibrated for Switzerland. Land cover and soil data come next.
- ERA5-Land is coarse. Radar rainfall would be better for local storms.
- This is a screening model for a demo, not a replacement for official hazard maps.
