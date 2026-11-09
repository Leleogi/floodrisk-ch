"""Simple event plots (matplotlib)."""

from __future__ import annotations

from pathlib import Path


def plot_event_runoff(ds, out_path: Path, title: str = "") -> Path:
    """Two-panel figure: hourly rain, and cumulative rain vs runoff (area mean over the AOI).

    `ds` is the Dataset returned by floodrisk.runoff.event_runoff.
    """
    import matplotlib

    matplotlib.use("Agg")  # no display needed
    import matplotlib.pyplot as plt

    time_dim = "valid_time" if "valid_time" in ds.dims else "time"
    spatial = [d for d in ds["precip_hourly_mm"].dims if d != time_dim]
    mean = ds.mean(spatial)
    t = mean[time_dim].values

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    ax1.bar(t, mean["precip_hourly_mm"].values, width=0.03, color="#3b82f6")
    ax1.set_ylabel("Rain (mm per hour)")
    ax1.set_title(title or "Event rain and runoff (area mean)")

    ax2.plot(t, mean["precip_cum_mm"].values, label="Cumulative rain", color="#3b82f6")
    ax2.plot(
        t,
        mean["runoff_cn_cum_mm"].values,
        label=f"Runoff, Curve Number {ds.attrs.get('curve_number', '?'):g}",
        color="#dc2626",
    )
    if "runoff_era5_cum_mm" in mean:
        ax2.plot(t, mean["runoff_era5_cum_mm"].values, label="Runoff, ERA5-Land model", color="#16a34a", ls="--")
    ax2.set_ylabel("Cumulative (mm)")
    ax2.set_xlabel("Time (UTC)")
    ax2.legend()
    fig.autofmt_xdate()
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
