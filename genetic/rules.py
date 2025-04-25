"""
rules.py

Modular rule construction and predicate logic for GA and trading strategies.
Exports: build_predicate, generate_random_rule, format_rule_text
"""
import pandas as pd
import numpy as np
import random
from typing import Tuple, List, Union

# Example RELATION_TYPES and thresholds (customize as needed)
RELATION_TYPES = ["gt", "lt", "cross_up", "cross_down", "between"]
THRESH_PCTL_LOW = 20
THRESH_PCTL_HIGH = 80
MAX_RULE_CONDITIONS = 5

def build_predicate(series: pd.Series, relation: str, threshold: Union[float, Tuple[float, float]]) -> pd.Series:
    """
    Build a boolean Series for a single predicate.
    Handles gt, lt, cross_up, cross_down, between.
    """
    if relation == "gt":
        return series > threshold
    elif relation == "lt":
        return series < threshold
    elif relation == "cross_up":
        # Cross above zero: signal when current > 0 and previous <= 0
        return (series > 0) & (series.shift(1) <= 0)
    elif relation == "cross_down":
        # Cross below zero: signal when current < 0 and previous >= 0
        return (series < 0) & (series.shift(1) >= 0)
    elif relation == "between":
        low, high = threshold
        return (series > low) & (series < high)
    else:
        raise ValueError(f"Unsupported relation type: {relation}")

def generate_random_rule(feat_df: pd.DataFrame, rng: random.Random) -> Tuple[pd.Series, str]:
    """
    Create a random AND-combined rule (boolean Series) plus readable text.
    Ported from iterate_strategies.py.
    """
    available_feats = list(feat_df.columns)
    num_conditions = rng.randint(1, MAX_RULE_CONDITIONS)
    chosen_feats = rng.sample(available_feats, num_conditions)

    cond_series_list: List[pd.Series] = []
    cond_texts: List[str] = []

    for feat in chosen_feats:
        series = feat_df[feat]
        relation = rng.choice(RELATION_TYPES)
        if relation == "cross_up":
            threshold = 0.0
        elif relation == "cross_down":
            threshold = 0.0
        elif relation == "between":
            low = np.nanpercentile(series.dropna(), THRESH_PCTL_LOW)
            high = np.nanpercentile(series.dropna(), THRESH_PCTL_HIGH)
            threshold = (low, high)
        else:
            perc = rng.choice([THRESH_PCTL_LOW, THRESH_PCTL_HIGH])
            threshold = np.nanpercentile(series.dropna(), perc)

        cond_series_list.append(build_predicate(series, relation, threshold))
        if relation == "between":
            cond_texts.append(f"({feat} between {threshold[0]:.4f} and {threshold[1]:.4f})")
        else:
            cond_texts.append(f"({feat} {relation} {threshold:.4f})")

    # Combine with logical AND, forward-fill to stay boolean when NaN due to lag
    combined = cond_series_list[0]
    for sr in cond_series_list[1:]:
        combined = combined & sr
    combined = combined.fillna(False)
    rule_text = " & ".join(cond_texts)
    return combined, rule_text

def format_rule_text(cond_texts: List[str]) -> str:
    """
    Format a rule as a human-readable string from a list of condition texts.
    """
    return " & ".join(cond_texts)
