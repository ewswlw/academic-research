## Defense First: A Multi-Asset Tactical Model for Adaptive Downside Protection

**Thomas D. Carlson**

## July 1, 2025

**Abstract:** In times of economic uncertainty, traditional “safe haven” portfolios—those heavily
invested in bonds or gold—have often failed to protect investors. This paper introduces _Defense
First_ , a simple but powerful strategy that adjusts monthly among four defensive assets: long-term
U.S. Treasury bonds (TLT), gold (GLD), broad commodities (DBC), and the U.S. dollar (UUP). It uses
a clear ranking system based on past performance to allocate to the strongest performers. When
one or more of these defensive assets falter, the position slots U.S. stocks (SPY) as a fallback
option.

Using data from 1986 to 2025, Defense First delivers better risk-adjusted returns than the stock
market, with lower volatility, smaller losses in downturns and low correlation to typical stock and
bond portfolios. The approach relies only on publicly available data and uses liquid, easy-to-trade
ETFs. This paper connects the strategy to academic research on momentum, crisis investing,
defensive rotation, and diversified portfolio design.

**Keywords:** Tactical Asset Allocation, Defensive Investing, Momentum Strategies, Crisis Alpha,
Risk Management, Adaptive Portfolios, Multi-Asset Strategy, Downside Protection, Macro
Hedging, Portfolio Construction

**1. Introduction**
Most portfolios, such as the traditional 60/40 split between equities and bonds, rely on static
diversification. However, during periods of market panic, asset correlations tend to rise and fixed
allocations can become vulnerable. Bonds, often seen as a hedge, have sometimes failed to
protect capital during dislocations driven by inflation or policy shocks.

Tail risk often manifests not as an isolated event but as a regime shift—disinflation to stagflation,
liquidity abundance to scarcity—at times rendering conventional hedges ineffective. This paper
proposes an adaptive, rules-based approach to tactical defense: Defense First.

Defense First rotates monthly among four distinct defensive asset classes, each aligned to a
different economic risk dimension: duration (TLT), monetary instability (GLD), inflation (DBC), and
dollar stress (UUP). These assets are selected via a momentum-based ranking system spanning
multiple time frames.

If any of these assets exhibit weaker momentum than cash (proxied by 90-day T-bills), their slot is
reallocated to U.S. equities (SPY) based on relative strength—not as a growth bet, but as the least
weak alternative.

This paper presents the model, evaluates long-term performance, and situates the approach
within existing academic and practitioner research.


**2. How the Strategy Works
Summary:** This section explains the logic behind choosing multiple defensive assets and the
mechanism through which Defense First selects them monthly.

**2.1 The Defensive Asset Framework**
Rather than relying on a single defensive tool, Defense First rotates among four macro-hedging
assets, each tied to a distinct risk regime:

- **TLT (Long-Term Treasuries)** : Excels during deflationary environments and Fed policy
    easing.
- **GLD (Gold)** : Responds positively to monetary instability and declining real rates.
- **DBC (Commodities)** : Performs during stagflation or commodity supply shocks.
- **UUP (U.S. Dollar Index)** : Rallies during global stress or funding crises as a liquidity haven.

This multi-asset structure ensures that Defense First adapts to different economic shocks rather
than relying on a single hedge. These assets are the core pool from which the model selects
monthly allocations based on momentum rankings and an absolute strength filter. If any asset
fails to show positive momentum relative to cash, its allocation shifts to equities (SPY).

**2.2 Monthly Allocation Mechanics**
Defense First employs momentum analysis over 1, 3, 6, and 12 months. Each defensive asset
receives an equal-weighted momentum score (25% for each timeframe). Portfolio allocation is
assigned as follows:

- Top-ranked asset: 40%
- Second: 30%
- Third: 20%
- Fourth: 10%
An absolute momentum filter is applied: if a defensive asset’s momentum is weaker than that of
90 - day T-bills, its allocation is redirected to SPY. This ensures capital is only deployed into strong
defensive assets.

**2.3 Data Used**
Where available, ETF data is used. For periods before ETF inception, data is supplemented with
Vanguard mutual funds, asset class indices, or futures proxies. This approach enables a long,
consistent returns history from 1986 to 2025.


**3. Performance and Risk Results
Summary:** This section presents empirical results from backtesting Defense First across market
cycles.

**3.1 Full Backtest Summary (1986–2025)**

```
Metric Defense First S&P 500
Annual Return (CAGR) 10.87% 11.17%
Volatility 8.50% 15.28%
Sharpe Ratio 0.89 0.
Sortino Ratio 1.59 0.
Best Year 27.46% 37.45%
Worst Year - 6.94% - 37.02%
Max Drawdown - 14.81% - 50.97%
Correlation with S&P 0.45 0.
% of Profitable Months 65.40% 65.61%
```
**3.2 Crisis Period Performance Summary**

```
Event Defense First S&P 500
Black Monday (1987) - 6.43% - 29.78%
Dotcom Bust (2000–2002) - 9.77% - 44.82%
Global Financial Crisis - 14.61% - 50.97%
COVID Crash (Q1 2020) 0.00% - 19.63%
Inflation Shock (2022) - 6.70% - 23.95%
```
**3.3 Trading Costs and Adjustments**
The model rebalances monthly with estimated turnover around 230% annually. Assuming a
conservative trading cost of 0.25% per trade, annualized returns decline by approximately 1.3%.
Even after costs, returns remain robust at ~9.59%.

**3.4 Why It’s Robust**

- Multiple momentum timeframes smooth short-term noise
- Absolute momentum screens avoid capital allocation to weak assets
- Equity fallback ensures no capital sits idle


**4. Where It Fits in a Portfolio
Summary:** This section outlines practical applications of Defense First within institutional and
retail portfolios.

**4.1 Roles in Asset Allocation Architecture**
Defense First addresses a common blind spot in strategic allocations: lack of adaptive defense. It
serves multiple roles:

- **Macro Diversifier** : Responds to shifting economic regimes
- **Crisis Mitigator** : Dynamically limits drawdowns
- **Risk-Off Core** : Generates positive expected return with lower volatility
- **Anti-Correlation Sleeve** : Low correlation to both equities and bonds, especially during
    systemic stress

**4.2 Real-World Considerations**
All components are liquid and tradable at scale using public ETFs. The strategy is implementable
using monthly closing prices and standard portfolio tools—no exotic data or hedge fund
infrastructure required.

**5. Research Foundations
Summary:** This section connects Defense First to established literature across momentum,
tactical allocation, and portfolio theory.

**5.1 Momentum Theory**
Momentum across asset classes is well-supported by empirical research. Jegadeesh & Titman
(1993) and Asness, Moskowitz, & Pedersen (2013) find that past winners often continue to
outperform.

**5.2 Tactical Allocation**
Faber (2007) and Keller & Butler (2015) explored trend-following systems and multi-momentum
frameworks. Defense First extends this research with monthly rankings among macro-hedging
assets.

**5.3 Handling Crisis Risk**
Kaminski & Lo (2014) and Ilmanen (2011) examine “crisis alpha”—return premia available during
market dislocations. Defense First leverages multiple tools beyond bonds to capture this alpha.

**5.4 Behavioral Finance**
Rule-based exits counteract behavioral biases identified by Kahneman & Tversky (1979),
particularly loss aversion and the disposition effect.

**5.5 Portfolio Design and Correlation**
Defense First modernizes frameworks like Harry Browne’s Permanent Portfolio and Ray Dalio’s All
Weather by dynamically allocating among uncorrelated assets using trend signals.


**6. Final Thoughts and Future Directions**
Defense First reframes defensive investing as a dynamic, data-driven process. Rather than relying
on static hedges, it adapts systematically to prevailing economic signals. The model is fully rules-
based, transparent, and implementable.

**Future enhancements could include:**

- Alternative risk-on fallback structures (e.g., 60/40, equity tactical or low-volatility tilt)
- International market applications
- Weight optimization beyond fixed 40/30/20/10 tiers
- Eliminating rebalancing trades within a threshold (e.g. +/- 5%) to save transaction cost
- Integration of macro or volatility regime filters

Defense First demonstrates an approach that is disciplined, scalable, and beneficial to modern
portfolio construction.


**Appendix A: Annual Returns Comparison (1986–2025)**

```
Year Defense First S&P 500
1986 18.80% 18.06%
1987 10.59% 4.71%
1988 12.66% 16.22%
1989 18.64% 31.36%
1990 - 1.46% - 3.32%
1991 24.96% 30.22%
1992 5.37% 7.42%
1993 9.25% 9.89%
1994 - 6.94% 1.18%
1995 27.46% 37.45%
1996 16.34% 22.88%
1997 20.30% 33.19%
1998 24.40% 28.62%
1999 10.88% 21.07%
2000 7.78% - 9.06%
2001 - 6.73% - 12.02%
2002 8.59% - 22.15%
2003 12.90% 28.50%
2004 15.87% 10.74%
2005 16.89% 4.77%
2006 11.57% 15.64%
2007 13.96% 5.39%
2008 5.69% - 37.02%
2009 7.36% 26.49%
2010 11.56% 14.91%
2011 12.95% 1.97%
2012 - 2.00% 15.82%
2013 16.32% 32.18%
2014 8.83% 13.51%
2015 - 1.67% 1.25%
2016 7.89% 11.82%
2017 4.82% 21.67%
2018 - 3.17% - 4.52%
2019 11.99% 31.33%
2020 20.10% 18.25%
2021 23.15% 28.53%
2022 8.07% - 18.23%
2023 7.00% 26.11%
2024 17.02% 24.84%
2025 13.92% 6.13%
```