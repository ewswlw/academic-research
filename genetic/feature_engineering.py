"""
feature_engineering.py

Modular feature engineering for trading strategies.
Exports: feature_engineering(df: pd.DataFrame) -> pd.DataFrame
"""
import pandas as pd
import numpy as np

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate engineered features for trading strategies.
    Args:
        df: Raw input DataFrame (e.g., prices, macro factors).
    Returns:
        pd.DataFrame: Engineered features with all necessary columns for rules.
    """
    """
    Feature engineering logic ported from iterate_strategies.py. Produces all features required by GA/rules.
    """
    feats = {}
    for col in df.columns:
        s = df[col]
        feats[f"{col}_z_6"] = (s - s.rolling(6).mean()) / (s.rolling(6).std() + 1e-8)
        feats[f"{col}_z_12"] = (s - s.rolling(12).mean()) / (s.rolling(12).std() + 1e-8)
        feats[f"{col}_sma_6"] = s.rolling(6).mean()
        feats[f"{col}_sma_12"] = s.rolling(12).mean()
        feats[f"{col}_pct_3"] = s.pct_change(3)
        feats[f"{col}_pct_12"] = s.pct_change(12)
        feats[f"{col}_clip"] = np.clip(s, -3, 3)
        feats[f"{col}_sqrt"] = np.sqrt(np.abs(s)) * np.sign(s)
        feats[f"{col}_square"] = np.square(s)
        feats[f"{col}_log1p"] = np.log1p(np.abs(s)) * np.sign(s)
    feats_df = pd.DataFrame(feats, index=df.index)
    # Optionally drop columns with too many NaNs
    feats_df = feats_df.dropna(axis=1, thresh=int(0.8 * len(feats_df)))
    print(f"[FeatureEngineering] Engineered features shape: {feats_df.shape}")
    return feats_df
