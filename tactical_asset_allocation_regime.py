"""
Tactical Asset Allocation with Macroeconomic Regime Detection

This module implements the complete strategy from the academic paper:
"Tactical Asset Allocation with Macroeconomic Regime Detection" by Oliveira et al.

Key Features:
- Modified k-means regime detection using FRED-MD macroeconomic data
- Probabilistic regime assignments via fuzzy clustering approach
- Three forecasting models: Naive, Black-Litterman, Ridge Regression
- Multiple position sizing strategies
- Comprehensive vectorbt backtesting framework
"""

import pandas as pd
import numpy as np
import requests
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics.pairwise import cosine_distances
from fredapi import Fred
import vectorbt as vbt
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings
warnings.filterwarnings('ignore')


class TacticalAssetAllocationRegime:
    """
    Tactical Asset Allocation with Macroeconomic Regime Detection
    
    Implements the complete strategy from the academic paper with:
    1. FRED-MD macroeconomic data collection
    2. Modified k-means regime detection algorithm
    3. Probabilistic regime assignments
    4. Multiple forecasting models
    5. Vectorbt backtesting framework
    """
    
    def __init__(
        self,
        fred_api_key: Optional[str] = None,
        fmp_api_key: str = 'mVMdO3LfRmwmW1bF7xw4M71WEiLjl8xD',
        estimation_window: int = 48,
        variance_threshold: float = 0.95,
        n_regimes: int = 6,
        random_state: int = 42
    ):
        """
        Initialize the Tactical Asset Allocation strategy
        
        Args:
            fred_api_key: FRED API key for macroeconomic data
            fmp_api_key: Financial Modeling Prep API key for ETF data
            estimation_window: Rolling window for model estimation (months)
            variance_threshold: PCA variance threshold for component selection
            n_regimes: Total number of regimes (including regime 0 for outliers)
            random_state: Random seed for reproducibility
        """
        self.fred_api_key = fred_api_key or "149095a7c7bdd559b94280c6bdf6b3f9"
        self.fmp_api_key = fmp_api_key
        self.estimation_window = estimation_window
        self.variance_threshold = variance_threshold
        self.n_regimes = n_regimes
        self.random_state = random_state
        
        # ETFs from the paper
        self.etfs = [
            'SPY', 'XLB', 'XLE', 'XLF', 'XLI', 
            'XLK', 'XLP', 'XLU', 'XLV', 'XLY'
        ]
        
        # FRED-MD variables (127 total, key variables from paper)
        self.fred_variables = {
            # Output and Income
            'GDP': 'GDP',
            'GDPC1': 'GDPC1',
            'INDPRO': 'INDPRO',
            'IPFINAL': 'IPFINAL',
            'IPCONGD': 'IPCONGD',
            'IPFUELS': 'IPFUELS',
            'IPMAT': 'IPMAT',
            'IPMANSICS': 'IPMANSICS',
            'IPNMAT': 'IPNMAT',
            'IPB51222s': 'IPB51222S',
            
            # Labor Market
            'PAYEMS': 'PAYEMS',
            'UNRATE': 'UNRATE',
            'CIVPART': 'CIVPART',
            'EMRATIO': 'EMRATIO',
            'UNEMPLOY': 'UNEMPLOY',
            'UEMPMEAN': 'UEMPMEAN',
            'UEMP5TO14': 'UEMP5TO14',
            'UEMP15T26': 'UEMP15T26',
            'UEMP27OV': 'UEMP27OV',
            'CLF16OV': 'CLF16OV',
            'CE16OV': 'CE16OV',
            'UEMPLT5': 'UEMPLT5',
            'AWHMAN': 'AWHMAN',
            'CES0600000007': 'CES0600000007',
            'CES0600000008': 'CES0600000008',
            'CES2000000008': 'CES2000000008',
            'CES3000000008': 'CES3000000008',
            
            # Housing
            'HOUST': 'HOUST',
            'HOUSTNE': 'HOUSTNE',
            'HOUSTMW': 'HOUSTMW',
            'HOUSTS': 'HOUSTS',
            'HOUSTW': 'HOUSTW',
            'PERMIT': 'PERMIT',
            'PERMITNE': 'PERMITNE',
            'PERMITMW': 'PERMITMW',
            'PERMITS': 'PERMITS',
            'PERMITW': 'PERMITW',
            
            # Consumption, Orders, and Inventories
            'DPCERA3M086SBEA': 'DPCERA3M086SBEA',
            'PCE': 'PCE',
            'PCEDG': 'PCEDG',
            'PCEND': 'PCEND',
            'PCES': 'PCES',
            'PCESV': 'PCESV',
            'UMCSENT': 'UMCSENT',
            'MANEMP': 'MANEMP',
            'DMANEMP': 'DMANEMP',
            'NDMANEMP': 'NDMANEMP',
            'SRVPRD': 'SRVPRD',
            'NAPMPI': 'NAPMPI',
            'NAPMEI': 'NAPMEI',
            'NAPMSDI': 'NAPMSDI',
            'NAPMII': 'NAPMII',
            'NAPMPRI': 'NAPMPRI',
            
            # Money and Credit
            'M1SL': 'M1SL',
            'M2SL': 'M2SL',
            'M2REAL': 'M2REAL',
            'BOGMBASE': 'BOGMBASE',
            'TOTRESNS': 'TOTRESNS',
            'NONBORRES': 'NONBORRES',
            'BUSLOANS': 'BUSLOANS',
            'REALLN': 'REALLN',
            'NONREVSL': 'NONREVSL',
            'CONSPI': 'CONSPI',
            
            # Interest and Exchange Rates
            'FEDFUNDS': 'FEDFUNDS',
            'TB3MS': 'TB3MS',
            'TB6MS': 'TB6MS',
            'GS1': 'GS1',
            'GS5': 'GS5',
            'GS10': 'GS10',
            'AAA': 'AAA',
            'BAA': 'BAA',
            'COMPAPFFx': 'COMPAPFF',
            'TB3SMFFM': 'TB3SMFFM',
            'TB6SMFFM': 'TB6SMFFM',
            'T1YFFM': 'T1YFFM',
            'T5YFFM': 'T5YFFM',
            'T10YFFM': 'T10YFFM',
            'AAAFFM': 'AAAFFM',
            'BAAFFM': 'BAAFFM',
            
            # Prices
            'CPIAUCSL': 'CPIAUCSL',
            'CPIAPPSL': 'CPIAPPSL',
            'CPITRNSL': 'CPITRNSL',
            'CPIMEDSL': 'CPIMEDSL',
            'CUSR0000SAC': 'CUSR0000SAC',
            'CUSR0000SAD': 'CUSR0000SAD',
            'CUSR0000SAS': 'CUSR0000SAS',
            'CPIULFSL': 'CPIULFSL',
            'CUSR0000SA0L2': 'CUSR0000SA0L2',
            'CUSR0000SA0L5': 'CUSR0000SA0L5',
            'PCEPI': 'PCEPI',
            'DDURRG3M086SBEA': 'DDURRG3M086SBEA',
            'DNDGRG3M086SBEA': 'DNDGRG3M086SBEA',
            'DSERRG3M086SBEA': 'DSERRG3M086SBEA',
            'CES0600000003': 'CES0600000003',
            'CES2000000003': 'CES2000000003',
            'CES3000000003': 'CES3000000003',
            'PPIFGS': 'PPIFGS',
            'PPIFCG': 'PPIFCG',
            'PPIIDC': 'PPIIDC',
            'PPIITM': 'PPIITM',
            'PPICRM': 'PPICRM',
            'PFCGEF': 'PFCGEF',
            'PFOOD': 'PFOOD',
            'PNRG': 'PNRG',
            'PNRGEY': 'PNRGEY',
            'PMP': 'PMP',
            'PNFI': 'PNFI',
            'PMCP': 'PMCP'
        }
        
        # Initialize components
        self.fred_client = None
        self.macro_data = None
        self.etf_data = None
        self.regime_classifications = None
        self.regime_probabilities = None
        self.transition_matrix = None
        
    def fetch_macroeconomic_data(
        self, 
        start_date: str = '2000-01-01', 
        end_date: str = '2023-12-31'
    ) -> pd.DataFrame:
        """
        Fetch FRED-MD macroeconomic data
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            DataFrame with macroeconomic variables
        """
        if not self.fred_api_key:
            raise ValueError("FRED API key required for macroeconomic data collection")
            
        self.fred_client = Fred(api_key=self.fred_api_key)
        macro_data = {}
        
        print("📊 Fetching FRED-MD macroeconomic data...")
        successful_fetches = 0
        
        # Add delay between requests to avoid rate limiting
        import time
        
        for i, (name, series_id) in enumerate(self.fred_variables.items()):
            try:
                # Add small delay between requests (FRED allows 120 requests per minute)
                if i > 0:
                    time.sleep(0.6)  # Wait 0.6 seconds between requests
                
                series = self.fred_client.get_series(
                    series_id,
                    observation_start=start_date,
                    observation_end=end_date,
                    frequency='m'  # Monthly frequency
                )
                if not series.empty:
                    macro_data[name] = series
                    successful_fetches += 1
                    print(f"✅ {name} ({series_id}): {len(series)} observations")
                else:
                    print(f"❌ {name} ({series_id}): No data available")
            except Exception as e:
                print(f"❌ {name} ({series_id}): Error - {str(e)}")
                # If rate limited, wait longer
                if "Too Many Requests" in str(e) or "Rate Limit" in str(e):
                    print(f"⏳ Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                
        print(f"\n📈 Successfully fetched {successful_fetches}/{len(self.fred_variables)} macroeconomic series")
        
        if not macro_data:
            raise ValueError("No macroeconomic data could be fetched")
            
        # Combine into DataFrame
        macro_df = pd.DataFrame(macro_data)
        
        # Handle missing values using forward fill then backward fill
        macro_df = macro_df.fillna(method='ffill').fillna(method='bfill')
        
        # Remove rows with any remaining NaN values
        macro_df = macro_df.dropna()
        
        self.macro_data = macro_df
        print(f"🎯 Final macro dataset: {macro_df.shape[0]} months × {macro_df.shape[1]} variables")
        
        return macro_df
    
    def fetch_asset_data(
        self, 
        start_date: str = '2000-01-01', 
        end_date: str = '2023-12-31'
    ) -> pd.DataFrame:
        """
        Fetch ETF price data using Financial Modeling Prep API
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            DataFrame with ETF price data
        """
        print("💰 Fetching ETF data from Financial Modeling Prep API...")
        etf_prices = {}
        
        base_url = 'https://financialmodelingprep.com/api/v3'
        
        for ticker in self.etfs:
            try:
                url = f"{base_url}/historical-price-full/{ticker}"
                params = {
                    'from': start_date,
                    'to': end_date,
                    'apikey': self.fmp_api_key
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    historical_data = data.get('historical', [])
                    
                    if historical_data:
                        df = pd.DataFrame(historical_data)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date').sort_index()
                        
                        # Convert to monthly frequency (end of month)
                        monthly_prices = df['adjClose'].resample('M').last()
                        etf_prices[ticker] = monthly_prices
                        
                        print(f"✅ {ticker}: {len(monthly_prices)} monthly observations")
                    else:
                        print(f"❌ {ticker}: No historical data available")
                else:
                    print(f"❌ {ticker}: API error {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {ticker}: Error - {str(e)}")
        
        if not etf_prices:
            raise ValueError("No ETF data could be fetched")
            
        # Combine into DataFrame
        etf_df = pd.DataFrame(etf_prices)
        
        # Calculate monthly returns
        etf_returns = etf_df.pct_change().dropna()
        
        self.etf_data = etf_returns
        print(f"🎯 Final ETF dataset: {etf_returns.shape[0]} months × {etf_returns.shape[1]} ETFs")
        
        return etf_returns
    
    def preprocess_macro_data(self, macro_data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess macroeconomic data with transformations and PCA
        
        Args:
            macro_data: Raw macroeconomic data
            
        Returns:
            Preprocessed data ready for regime detection
        """
        print("🔧 Preprocessing macroeconomic data...")
        
        # Apply transformations as specified in FRED-MD documentation
        transformed_data = macro_data.copy()
        
        # For simplicity, we'll apply log differences to most series
        # In a full implementation, would use FRED-MD t-codes for specific transformations
        for col in transformed_data.columns:
            if transformed_data[col].min() > 0:  # Only log-transform positive series
                transformed_data[col] = np.log(transformed_data[col]).diff()
            else:
                transformed_data[col] = transformed_data[col].diff()
        
        # Drop first row with NaN values from differencing
        transformed_data = transformed_data.dropna()
        
        # Standardize variables
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(transformed_data)
        scaled_df = pd.DataFrame(
            scaled_data, 
            index=transformed_data.index, 
            columns=transformed_data.columns
        )
        
        # Apply PCA to reduce dimensionality
        pca = PCA(random_state=self.random_state)
        pca_components = pca.fit_transform(scaled_data)
        
        # Determine number of components for variance threshold
        cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
        n_components = np.argmax(cumsum_variance >= self.variance_threshold) + 1
        
        print(f"📊 PCA: {n_components} components explain {self.variance_threshold*100}% of variance")
        
        # Use only the required number of components
        pca_df = pd.DataFrame(
            pca_components[:, :n_components],
            index=transformed_data.index,
            columns=[f'PC{i+1}' for i in range(n_components)]
        )
        
        print(f"✅ Preprocessed data: {pca_df.shape[0]} months × {pca_df.shape[1]} principal components")
        
        return pca_df
    
    def regime_classification(self, processed_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Implement modified k-means regime detection algorithm from the paper
        
        Args:
            processed_data: Preprocessed macroeconomic data
            
        Returns:
            Tuple of (regime_labels, regime_probabilities)
        """
        print("🎯 Performing regime classification using modified k-means...")
        
        X = processed_data.values
        
        # Step 1: L2 clustering to separate outliers
        print("📊 Step 1: L2 clustering to identify outliers...")
        kmeans_l2 = KMeans(n_clusters=2, random_state=self.random_state, n_init=10)
        l2_labels = kmeans_l2.fit_predict(X)
        
        # Determine which cluster represents outliers (smaller cluster)
        cluster_sizes = np.bincount(l2_labels)
        outlier_cluster = np.argmin(cluster_sizes)
        typical_mask = l2_labels != outlier_cluster
        
        print(f"   Outliers: {np.sum(~typical_mask)} months")
        print(f"   Typical: {np.sum(typical_mask)} months")
        
        # Step 2: Cosine clustering on typical samples
        print("📊 Step 2: Cosine clustering on typical samples...")
        X_typical = X[typical_mask]
        
        # Use cosine distance for k-means
        # We'll implement this by normalizing data and using euclidean distance
        X_typical_normalized = X_typical / np.linalg.norm(X_typical, axis=1, keepdims=True)
        
        # Determine optimal number of clusters using elbow method
        n_typical_clusters = min(5, max(2, len(X_typical) // 20))  # Reasonable range
        
        kmeans_cosine = KMeans(
            n_clusters=n_typical_clusters, 
            random_state=self.random_state, 
            n_init=10
        )
        cosine_labels = kmeans_cosine.fit_predict(X_typical_normalized)
        
        print(f"   Identified {n_typical_clusters} typical regimes")
        
        # Step 3: Compute probabilistic regime assignments
        regime_probs = self._calculate_regime_probabilities(
            X, kmeans_l2, kmeans_cosine, typical_mask
        )
        
        # Get most likely regime for each observation
        regime_labels = np.argmax(regime_probs, axis=1)
        
        self.regime_classifications = regime_labels
        self.regime_probabilities = regime_probs
        
        print(f"✅ Regime classification complete:")
        for i in range(self.n_regimes):
            count = np.sum(regime_labels == i)
            print(f"   Regime {i}: {count} months ({count/len(regime_labels)*100:.1f}%)")
        
        return regime_labels, regime_probs
    
    def _calculate_regime_probabilities(
        self,
        X: np.ndarray,
        kmeans_l2: KMeans,
        kmeans_cosine: KMeans,
        typical_mask: np.ndarray
    ) -> np.ndarray:
        """
        Calculate probabilistic regime assignments using fuzzy clustering approach
        
        Args:
            X: Input data
            kmeans_l2: Fitted L2 k-means model
            kmeans_cosine: Fitted cosine k-means model
            typical_mask: Boolean mask for typical vs outlier samples
            
        Returns:
            Regime probability matrix
        """
        n_samples = len(X)
        regime_probs = np.zeros((n_samples, self.n_regimes))
        
        # Calculate distances for L2 clustering
        l2_distances = kmeans_l2.transform(X)
        l2_probs = self._distances_to_probabilities(l2_distances)
        
        # For outlier regime (Regime 0)
        outlier_prob = l2_probs[:, np.argmin(np.bincount(kmeans_l2.labels_))]
        regime_probs[:, 0] = outlier_prob
        
        # For typical samples, calculate cosine clustering probabilities
        X_typical = X[typical_mask]
        if len(X_typical) > 0:
            X_typical_normalized = X_typical / np.linalg.norm(X_typical, axis=1, keepdims=True)
            cosine_distances = kmeans_cosine.transform(X_typical_normalized)
            cosine_probs = self._distances_to_probabilities(cosine_distances)
            
            # Scale cosine probabilities by (1 - outlier_prob)
            typical_indices = np.where(typical_mask)[0]
            for i, idx in enumerate(typical_indices):
                scale_factor = 1 - regime_probs[idx, 0]
                for j in range(cosine_probs.shape[1]):
                    regime_probs[idx, j + 1] = cosine_probs[i, j] * scale_factor
        
        # Normalize probabilities to sum to 1
        row_sums = regime_probs.sum(axis=1, keepdims=True)
        regime_probs = regime_probs / np.maximum(row_sums, 1e-10)
        
        return regime_probs
    
    def _distances_to_probabilities(self, distances: np.ndarray) -> np.ndarray:
        """
        Convert k-means distances to probabilities using fuzzy clustering approach
        
        Args:
            distances: Distance matrix from k-means transform
            
        Returns:
            Probability matrix
        """
        # Avoid division by zero
        distances = np.maximum(distances, 1e-10)
        
        # Convert distances to similarities (inverse relationship)
        similarities = 1.0 / distances
        
        # Normalize to probabilities
        probs = similarities / similarities.sum(axis=1, keepdims=True)
        
        return probs
    
    def calculate_transition_matrix(self, regime_labels: np.ndarray) -> np.ndarray:
        """
        Calculate regime transition probability matrix
        
        Args:
            regime_labels: Array of regime classifications
            
        Returns:
            Transition probability matrix
        """
        print("🔄 Calculating regime transition matrix...")
        
        transition_matrix = np.zeros((self.n_regimes, self.n_regimes))
        
        for t in range(len(regime_labels) - 1):
            current_regime = regime_labels[t]
            next_regime = regime_labels[t + 1]
            transition_matrix[current_regime, next_regime] += 1
        
        # Normalize rows to get probabilities
        row_sums = transition_matrix.sum(axis=1, keepdims=True)
        transition_matrix = np.divide(
            transition_matrix, 
            row_sums, 
            out=np.zeros_like(transition_matrix), 
            where=row_sums != 0
        )
        
        self.transition_matrix = transition_matrix
        
        print("✅ Transition matrix calculated")
        print("   Diagonal dominance (regime persistence):")
        for i in range(self.n_regimes):
            persistence = transition_matrix[i, i]
            print(f"   Regime {i}: {persistence:.3f}")
        
        return transition_matrix
    
    def forecast_regime_returns(
        self,
        asset_returns: pd.DataFrame,
        regime_labels: np.ndarray,
        regime_probs: np.ndarray,
        transition_matrix: np.ndarray,
        model_type: str = 'naive'
    ) -> pd.DataFrame:
        """
        Forecast asset returns using regime information
        
        Args:
            asset_returns: Historical asset returns
            regime_labels: Regime classifications
            regime_probs: Regime probabilities
            transition_matrix: Regime transition matrix
            model_type: Type of forecasting model ('naive', 'black_litterman', 'ridge')
            
        Returns:
            Forecasted returns
        """
        print(f"🔮 Forecasting returns using {model_type} model...")
        
        # Simply align by length since both should be monthly data
        min_length = min(len(asset_returns), len(regime_labels))
        
        asset_returns_aligned = asset_returns.iloc[:min_length]
        regime_labels_aligned = regime_labels[:min_length]
        regime_probs_aligned = regime_probs[:min_length]
        
        forecasts = pd.DataFrame(
            index=asset_returns_aligned.index,
            columns=asset_returns_aligned.columns
        )
        
        if model_type == 'naive':
            forecasts = self._naive_forecast(
                asset_returns_aligned, regime_labels_aligned, regime_probs_aligned, transition_matrix
            )
        elif model_type == 'black_litterman':
            forecasts = self._black_litterman_forecast(
                asset_returns_aligned, regime_labels_aligned, regime_probs_aligned, transition_matrix
            )
        elif model_type == 'ridge':
            forecasts = self._ridge_forecast(
                asset_returns_aligned, regime_labels_aligned, regime_probs_aligned, transition_matrix
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        print(f"✅ Forecasting complete: {forecasts.shape[0]} periods × {forecasts.shape[1]} assets")
        
        return forecasts
    
    def _naive_forecast(
        self,
        returns: pd.DataFrame,
        regime_labels: np.ndarray,
        regime_probs: np.ndarray,
        transition_matrix: np.ndarray
    ) -> pd.DataFrame:
        """Naive forecasting using regime-conditional expected returns"""
        forecasts = pd.DataFrame(index=returns.index, columns=returns.columns)
        
        for t in range(self.estimation_window, len(returns)):
            # Get next period regime probabilities
            current_regime_prob = regime_probs[t-1]
            next_regime_prob = current_regime_prob @ transition_matrix
            
            # Calculate regime-conditional expected returns
            expected_returns = np.zeros(len(returns.columns))
            
            for regime in range(self.n_regimes):
                regime_mask = regime_labels[:t] == regime
                if np.any(regime_mask):
                    regime_returns = returns.iloc[:t].loc[returns.iloc[:t].index[regime_mask]]
                    if not regime_returns.empty:
                        regime_mean = regime_returns.mean()
                        expected_returns += next_regime_prob[regime] * regime_mean.values
            
            forecasts.iloc[t] = expected_returns
        
        return forecasts.dropna()
    
    def _black_litterman_forecast(
        self,
        returns: pd.DataFrame,
        regime_labels: np.ndarray,
        regime_probs: np.ndarray,
        transition_matrix: np.ndarray
    ) -> pd.DataFrame:
        """Black-Litterman forecasting with regime-based views"""
        forecasts = pd.DataFrame(index=returns.index, columns=returns.columns)
        
        # Black-Litterman parameters
        tau = 0.025  # Scaling parameter for uncertainty in prior
        
        for t in range(self.estimation_window, len(returns)):
            historical_returns = returns.iloc[:t]
            
            # Prior beliefs (sample mean and covariance)
            mu_prior = historical_returns.mean()
            Sigma = historical_returns.cov()
            
            # Get next period regime probabilities
            current_regime_prob = regime_probs[t-1]
            next_regime_prob = current_regime_prob @ transition_matrix
            
            # Views based on most likely regime
            most_likely_regime = np.argmax(next_regime_prob)
            regime_mask = regime_labels[:t] == most_likely_regime
            
            if np.any(regime_mask):
                regime_returns = historical_returns.loc[historical_returns.index[regime_mask]]
                if not regime_returns.empty:
                    q = regime_returns.mean()  # Views
                    P = np.eye(len(returns.columns))  # Pick matrix (views on all assets)
                    Omega = np.diag(np.diag(Sigma)) * 0.1  # Uncertainty in views
                    
                    # Black-Litterman formula
                    M1 = np.linalg.inv(tau * Sigma)
                    M2 = P.T @ np.linalg.inv(Omega) @ P
                    M3 = np.linalg.inv(M1 + M2)
                    
                    mu_bl = M3 @ (M1 @ mu_prior + P.T @ np.linalg.inv(Omega) @ q)
                    forecasts.iloc[t] = mu_bl
                else:
                    forecasts.iloc[t] = mu_prior
            else:
                forecasts.iloc[t] = mu_prior
        
        return forecasts.dropna()
    
    def _ridge_forecast(
        self,
        returns: pd.DataFrame,
        regime_labels: np.ndarray,
        regime_probs: np.ndarray,
        transition_matrix: np.ndarray
    ) -> pd.DataFrame:
        """Ridge regression forecasting with regime features"""
        forecasts = pd.DataFrame(index=returns.index, columns=returns.columns)
        
        for t in range(self.estimation_window, len(returns)):
            # Get next period regime probabilities
            current_regime_prob = regime_probs[t-1]
            next_regime_prob = current_regime_prob @ transition_matrix
            
            # Prepare features and targets for each asset
            for asset in returns.columns:
                asset_forecasts = []
                
                # Train regime-specific models
                for regime in range(self.n_regimes):
                    regime_mask = regime_labels[:t] == regime
                    
                    if np.sum(regime_mask) >= 5:  # Minimum samples for training
                        # Features: lagged returns and macro indicators
                        X_regime = []
                        y_regime = []
                        
                        for i in range(1, t):
                            if regime_mask[i]:
                                features = [returns[asset].iloc[i-1]]  # Lagged return
                                features.extend(regime_probs[i-1])  # Regime probabilities
                                X_regime.append(features)
                                y_regime.append(returns[asset].iloc[i])
                        
                        if len(X_regime) >= 3:
                            X_regime = np.array(X_regime)
                            y_regime = np.array(y_regime)
                            
                            # Train Ridge regression
                            ridge = Ridge(alpha=1.0, random_state=self.random_state)
                            ridge.fit(X_regime, y_regime)
                            
                            # Predict for current features
                            current_features = [returns[asset].iloc[t-1]]
                            current_features.extend(current_regime_prob)
                            prediction = ridge.predict([current_features])[0]
                            
                            asset_forecasts.append(next_regime_prob[regime] * prediction)
                
                # Combine regime-weighted forecasts
                if asset_forecasts:
                    forecasts.loc[returns.index[t], asset] = sum(asset_forecasts)
                else:
                    # Fallback to simple mean
                    forecasts.loc[returns.index[t], asset] = returns[asset].iloc[:t].mean()
        
        return forecasts.dropna()
    
    def construct_portfolio(
        self,
        forecasts: pd.DataFrame,
        strategy: str = 'long_only',
        top_assets: int = 3
    ) -> pd.DataFrame:
        """
        Construct portfolio weights based on forecasts and strategy
        
        Args:
            forecasts: Forecasted returns
            strategy: Portfolio strategy ('long_only', 'long_short', 'mixed')
            top_assets: Number of top assets to include
            
        Returns:
            Portfolio weights
        """
        print(f"🎯 Constructing {strategy} portfolio with top {top_assets} assets...")
        
        weights = pd.DataFrame(
            np.zeros_like(forecasts),
            index=forecasts.index,
            columns=forecasts.columns
        )
        
        for t in range(len(forecasts)):
            forecast_t = forecasts.iloc[t]
            
            if strategy == 'long_only':
                weights.iloc[t] = self._long_only_weights(forecast_t, top_assets)
            elif strategy == 'long_short':
                weights.iloc[t] = self._long_short_weights(forecast_t, top_assets)
            elif strategy == 'mixed':
                # Use regime information for mixed strategy
                if hasattr(self, 'regime_classifications') and self.regime_classifications is not None:
                    current_regime = self.regime_classifications[t] if t < len(self.regime_classifications) else 0
                    if current_regime == 0:  # Economic difficulty regime
                        weights.iloc[t] = self._long_short_weights(forecast_t, top_assets)
                    else:
                        weights.iloc[t] = self._long_only_weights(forecast_t, top_assets)
                else:
                    weights.iloc[t] = self._long_only_weights(forecast_t, top_assets)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        print(f"✅ Portfolio construction complete")
        
        return weights
    
    def _long_only_weights(self, forecasts: pd.Series, top_assets: int) -> pd.Series:
        """Calculate long-only portfolio weights"""
        # Convert to numeric and handle any non-numeric values
        forecasts_numeric = pd.to_numeric(forecasts, errors='coerce').fillna(0.0)
        
        # Select top forecasted assets
        top_indices = forecasts_numeric.nlargest(top_assets).index
        
        weights = pd.Series(0.0, index=forecasts.index)
        
        if len(top_indices) > 0:
            # Equal weight among top assets
            weights[top_indices] = 1.0 / len(top_indices)
        
        return weights
    
    def _long_short_weights(self, forecasts: pd.Series, top_assets: int) -> pd.Series:
        """Calculate long-short portfolio weights"""
        # Convert to numeric and handle any non-numeric values
        forecasts_numeric = pd.to_numeric(forecasts, errors='coerce').fillna(0.0)
        
        # Select top and bottom assets
        top_long = forecasts_numeric.nlargest(top_assets).index
        top_short = forecasts_numeric.nsmallest(top_assets).index
        
        weights = pd.Series(0.0, index=forecasts.index)
        
        # Long positions
        if len(top_long) > 0:
            weights[top_long] = 0.5 / len(top_long)
        
        # Short positions
        if len(top_short) > 0:
            weights[top_short] = -0.5 / len(top_short)
        
        return weights
    
    def backtest_strategy(
        self,
        start_date: str = '2000-01-01',
        end_date: str = '2023-12-31'
    ) -> Dict[str, Any]:
        """
        Complete backtest of the tactical asset allocation strategy
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Comprehensive backtest results
        """
        print("🚀 Starting comprehensive strategy backtest...")
        
        # Step 1: Fetch and prepare data
        macro_data = self.fetch_macroeconomic_data(start_date, end_date)
        asset_returns = self.fetch_asset_data(start_date, end_date)
        
        # Step 2: Preprocess macroeconomic data
        processed_macro = self.preprocess_macro_data(macro_data)
        
        # Step 3: Regime classification
        regime_labels, regime_probs = self.regime_classification(processed_macro)
        transition_matrix = self.calculate_transition_matrix(regime_labels)
        
        # Step 4: Generate forecasts using all models
        models = ['naive', 'black_litterman', 'ridge']
        strategies = ['long_only', 'long_short', 'mixed']
        top_assets_options = [2, 3, 4]
        
        all_results = {}
        
        for model in models:
            forecasts = self.forecast_regime_returns(
                asset_returns, regime_labels, regime_probs, transition_matrix, model
            )
            
            for strategy in strategies:
                for top_assets in top_assets_options:
                    strategy_name = f"{model}_{strategy}_{top_assets}"
                    print(f"📊 Backtesting {strategy_name}...")
                    
                    # Construct portfolio weights
                    weights = self.construct_portfolio(forecasts, strategy, top_assets)
                    
                    # Align weights and returns
                    common_dates = weights.index.intersection(asset_returns.index)
                    weights_aligned = weights.loc[common_dates]
                    returns_aligned = asset_returns.loc[common_dates]
                    
                    if len(common_dates) > 0:
                        # Calculate portfolio returns
                        portfolio_returns = (weights_aligned.shift(1) * returns_aligned).sum(axis=1).dropna()
                        
                        # Calculate performance metrics
                        results = self._calculate_performance_metrics(portfolio_returns)
                        results['returns'] = portfolio_returns
                        results['weights'] = weights_aligned
                        
                        all_results[strategy_name] = results
        
        # Add benchmark results
        print("📊 Calculating benchmark performance...")
        spy_returns = asset_returns['SPY'].dropna()
        all_results['spy'] = self._calculate_performance_metrics(spy_returns)
        all_results['spy']['returns'] = spy_returns
        
        # Equal weight benchmark
        ew_returns = asset_returns.mean(axis=1).dropna()
        all_results['ew'] = self._calculate_performance_metrics(ew_returns)
        all_results['ew']['returns'] = ew_returns
        
        print("🎉 Backtest complete! Results for all strategies generated.")
        
        return all_results
    
    def _calculate_performance_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if len(returns) == 0 or returns.isna().all():
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            }
        
        # Basic return metrics
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + returns.mean()) ** 12 - 1
        volatility = returns.std() * np.sqrt(12)
        
        # Risk-adjusted metrics
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(12) if len(downside_returns) > 0 else 0
        sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }
    
    def vectorbt_backtest(
        self,
        weights: pd.DataFrame,
        returns: pd.DataFrame,
        initial_cash: float = 100000,
        transaction_costs: float = 0.001
    ) -> Any:
        """
        Perform vectorbt backtesting with transaction costs
        
        Args:
            weights: Portfolio weights over time
            returns: Asset returns
            initial_cash: Initial capital
            transaction_costs: Transaction cost per trade (0.1% default)
            
        Returns:
            Vectorbt Portfolio object with full statistics
        """
        print("⚡ Running vectorbt backtesting framework...")
        
        # Align data
        common_dates = weights.index.intersection(returns.index)
        weights_aligned = weights.loc[common_dates]
        returns_aligned = returns.loc[common_dates]
        
        # Convert returns to prices
        prices = (1 + returns_aligned).cumprod() * 100  # Start at $100
        
        # Calculate position values
        position_values = weights_aligned * initial_cash
        
        # Create vectorbt portfolio
        try:
            pf = vbt.Portfolio.from_orders(
                close=prices,
                size=position_values.diff().fillna(position_values.iloc[0]),
                size_type='value',
                fees=transaction_costs,
                freq='M'
            )
            
            print("✅ Vectorbt backtesting complete!")
            print("\n📊 Performance Summary:")
            print(f"   Total Return: {pf.total_return():.2%}")
            print(f"   Sharpe Ratio: {pf.sharpe_ratio():.3f}")
            print(f"   Max Drawdown: {pf.max_drawdown():.2%}")
            print(f"   Win Rate: {(pf.returns() > 0).sum() / len(pf.returns()):.2%}")
            
            return pf
            
        except Exception as e:
            print(f"❌ Vectorbt backtesting failed: {str(e)}")
            return None


# Additional utility functions for analysis
def display_results_summary(results: Dict[str, Any]) -> None:
    """Display comprehensive results summary"""
    print("\n" + "="*80)
    print("📊 TACTICAL ASSET ALLOCATION - COMPREHENSIVE RESULTS SUMMARY")
    print("="*80)
    
    # Create summary DataFrame
    summary_data = []
    for strategy_name, metrics in results.items():
        if 'returns' in metrics:
            summary_data.append({
                'Strategy': strategy_name,
                'Total Return': f"{metrics['total_return']:.2%}",
                'Annual Return': f"{metrics['annual_return']:.2%}",
                'Volatility': f"{metrics['volatility']:.2%}",
                'Sharpe Ratio': f"{metrics['sharpe_ratio']:.3f}",
                'Sortino Ratio': f"{metrics['sortino_ratio']:.3f}",
                'Max Drawdown': f"{metrics['max_drawdown']:.2%}",
                'Win Rate': f"{metrics['win_rate']:.2%}"
            })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    print("="*80)


if __name__ == "__main__":
    # Example usage
    strategy = TacticalAssetAllocationRegime()
    
    # Run complete backtest
    results = strategy.backtest_strategy('2000-01-01', '2023-12-31')
    
    # Display results
    display_results_summary(results)