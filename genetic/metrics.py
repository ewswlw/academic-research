"""Performance & risk helpers"""

import numpy as np
import pandas as pd


def equity_curve(returns: pd.Series) -> pd.Series:
    return (1 + returns).cumprod()


def cagr(returns: pd.Series) -> float:
    years = len(returns) / 12
    total_ret = equity_curve(returns).iloc[-1]
    return total_ret ** (1 / years) - 1


def max_drawdown(returns: pd.Series) -> float:
    ec = equity_curve(returns)
    roll_max = ec.cummax()
    dd = (ec / roll_max) - 1
    return dd.min()
