"""
Feature engineering
-------------------
Generates lag‑1 features (momentum, MAs, volatility, z‑scores, etc.).
All features are shifted +1 month to avoid look‑ahead bias.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def _rolling_zscore(series: pd.Series, win: int = 12) -> pd.Series:
    mu = series.rolling(win).mean()
    sigma = series.rolling(win).std()
    return (series - mu) / sigma


def build_features(price: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    df = pd.DataFrame({"price": price})
    # momentum k=1..10
    for k in range(1, 11):
        df[f"mom_{k}"] = price.pct_change(k)
    # SMAs & EMAs 2..10
    for k in range(2, 11):
        df[f"sma_{k}"] = price.rolling(k).mean()
        df[f"ema_{k}"] = price.ewm(span=k, adjust=False).mean()
        df[f"px_div_sma_{k}"] = price / df[f"sma_{k}"] - 1
        df[f"px_div_ema_{k}"] = price / df[f"ema_{k}"] - 1
    # crossover dummy (fast 2‑5 vs slow 6‑10)
    df["ma_cross"] = (
        df[[f"sma_{k}" for k in range(2, 6)]].mean(axis=1)
        > df[[f"sma_{k}" for k in range(6, 11)]].mean(axis=1)
    ).astype(int)
    # volatility features
    df["roll_vol_6"] = price.pct_change().rolling(6).std()
    df["roll_vol_12"] = price.pct_change().rolling(12).std()
    df["cv_12"] = df["roll_vol_12"] / price.pct_change().rolling(12).mean().abs()
    # z‑scores
    df["z_ret_12"] = _rolling_zscore(price.pct_change(), 12)
    df["z_pxchg_12"] = _rolling_zscore(price.diff(), 12)

    # Lag everything by 1
    df = df.shift(1).dropna()
    y = price.pct_change().apply(np.log1p).loc[df.index]  # aligned target
    # optional PCA to 3 comps
    feat_cols = df.columns.tolist()
    scaler = StandardScaler()
    pca = PCA(n_components=3)
    comps = pca.fit_transform(scaler.fit_transform(df[feat_cols]))
    df[[f"pca_{i+1}" for i in range(3)]] = comps
    return df, y
