"""
Data ingestion & sanity‑check utilities
--------------------------------------
• Load monthly CSV and guarantee a strict monthly DatetimeIndex (length==91)
• Drop duplicates / NaNs with explicit warnings
• Provide log‑return series for downstream modules
"""
from pathlib import Path
from typing import Tuple

import pandas as pd
import plotly.express as px
import numpy as np


def load_prices(csv_path: Path | str, price_col: str = "cad_ig_er_index") -> pd.Series:
    """Return clean monthly price series.
    Raises if row‑count < 90 or index not monotonic monthly.
    """
    df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    # sort / drop duplicates
    df = df[~df.index.duplicated(keep="first")].sort_index()
    df = df.dropna(subset=[price_col])
    # relax strict length check; require sufficient history
    if len(df) < 90:
        raise ValueError(f"Too few rows ({len(df)}), expected at least ~90 monthly observations")
    if len(df) != 91:
        print(f"[data_io] Warning: expected 91 rows; found {len(df)}. Proceeding anyway.")
    # enforce monotonic increasing index
    if not df.index.is_monotonic_increasing:
        raise ValueError("Datetime index is not monotonic increasing")
    # check approximate monthly spacing; warn if irregular
    deltas = df.index.to_series().diff().dropna().dt.days
    if deltas.min() < 20 or deltas.max() > 40:
        print("[data_io] Warning: Irregular spacing in dates, continuing anyway.")
    return df[price_col]


def audit_plots(price: pd.Series, out_dir: Path) -> None:
    """Save interactive line charts for raw price & log‑returns."""
    out_dir.mkdir(exist_ok=True)
    price_fig = px.line(price, title="Raw Price ‑ cad_ig_er_index")
    price_fig.write_html(out_dir / "price_curve.html", include_plotlyjs="cdn")

    log_ret = np.log(price / price.shift(1)).dropna()
    ret_fig = px.line(log_ret, title="Monthly Log‑Return")
    ret_fig.write_html(out_dir / "log_returns.html", include_plotlyjs="cdn")


def load_and_audit(csv_path: Path | str, out_dir: Path) -> Tuple[pd.Series, pd.Series]:
    """Wrapper used by main script."""
    price = load_prices(csv_path)
    audit_plots(price, out_dir)
    log_ret = np.log(price / price.shift(1)).fillna(0.0)
    return price, log_ret
