import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import the strategy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tactical_asset_allocation_regime import TacticalAssetAllocationRegime

class TestTacticalAssetAllocationRegime:
    """Test cases for the Tactical Asset Allocation Regime strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a strategy instance for testing"""
        return TacticalAssetAllocationRegime(fred_api_key="test_key")
    
    @pytest.fixture
    def sample_macro_data(self):
        """Create sample macroeconomic data"""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='M')
        np.random.seed(42)
        
        data = {
            'GDP': np.random.randn(len(dates)).cumsum() + 100,
            'CPI': np.random.randn(len(dates)).cumsum() + 200,
            'UNRATE': np.random.uniform(3, 8, len(dates)),
            'FEDFUNDS': np.random.uniform(0, 5, len(dates)),
            'INDPRO': np.random.randn(len(dates)).cumsum() + 100,
            'PAYEMS': np.random.randn(len(dates)).cumsum() + 150000,
            'PCE': np.random.randn(len(dates)).cumsum() + 15000,
            'M2SL': np.random.randn(len(dates)).cumsum() + 20000,
            'HOUST': np.random.uniform(1000, 2000, len(dates)),
            'UMCSENT': np.random.uniform(50, 100, len(dates))
        }
        
        return pd.DataFrame(data, index=dates)
    
    @pytest.fixture
    def sample_asset_data(self):
        """Create sample asset return data"""
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='M')
        np.random.seed(42)
        
        etfs = [
            'SPY US Equity', 'XLB US Equity', 'XLE US Equity', 'XLF US Equity',
            'XLI US Equity', 'XLK US Equity', 'XLP US Equity', 'XLU US Equity',
            'XLV US Equity', 'XLY US Equity'
        ]
        
        data = {}
        for etf in etfs:
            # Generate realistic monthly returns
            returns = np.random.normal(0.01, 0.05, len(dates))
            data[etf] = returns
            
        return pd.DataFrame(data, index=dates)
    
    def test_initialization(self, strategy):
        """Test strategy initialization"""
        assert strategy.etfs == [
            'SPY US Equity', 'XLB US Equity', 'XLE US Equity', 'XLF US Equity',
            'XLI US Equity', 'XLK US Equity', 'XLP US Equity', 'XLU US Equity',
            'XLV US Equity', 'XLY US Equity'
        ]
        assert strategy.estimation_window == 48
        assert strategy.variance_threshold == 0.95
        assert strategy.n_regimes == 6
    
    @patch('tactical_asset_allocation_regime.Fred')
    def test_fetch_macroeconomic_data(self, mock_fred, strategy):
        """Test macroeconomic data fetching"""
        # Mock FRED API response
        mock_fred_instance = Mock()
        mock_fred_instance.get_series.return_value = pd.Series(
            np.random.randn(48), 
            index=pd.date_range('2020-01-01', periods=48, freq='M')
        )
        mock_fred.return_value = mock_fred_instance
        
        data = strategy.fetch_macroeconomic_data('2020-01-01', '2023-12-31')
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert 'GDP' in data.columns
    
    @patch('tactical_asset_allocation_regime.xbbg')
    def test_fetch_asset_data(self, mock_xbbg, strategy):
        """Test asset data fetching"""
        # Mock Bloomberg response
        mock_xbbg.bdh.return_value = pd.Series(
            np.random.uniform(100, 200, 48),
            index=pd.date_range('2020-01-01', periods=48, freq='M')
        )
        
        data = strategy.fetch_asset_data('2020-01-01', '2023-12-31')
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
    
    def test_preprocess_macro_data(self, strategy, sample_macro_data):
        """Test macroeconomic data preprocessing"""
        processed_data = strategy.preprocess_macro_data(sample_macro_data)
        
        assert isinstance(processed_data, pd.DataFrame)
        assert len(processed_data) == len(sample_macro_data)
        assert processed_data.shape[1] <= sample_macro_data.shape[1]  # PCA reduces dimensions
    
    def test_regime_classification(self, strategy, sample_macro_data):
        """Test regime classification"""
        processed_data = strategy.preprocess_macro_data(sample_macro_data)
        regime_labels, regime_probs = strategy.regime_classification(processed_data)
        
        assert isinstance(regime_labels, np.ndarray)
        assert isinstance(regime_probs, np.ndarray)
        assert len(regime_labels) == len(processed_data)
        assert regime_probs.shape == (len(processed_data), 6)  # 6 regimes
        assert np.all(regime_labels >= 0) and np.all(regime_labels <= 5)
        assert np.allclose(regime_probs.sum(axis=1), 1.0, atol=1e-10)  # Probabilities sum to 1
    
    def test_calculate_transition_matrix(self, strategy):
        """Test transition matrix calculation"""
        # Create sample regime labels
        regime_labels = np.array([0, 1, 2, 1, 0, 2, 1, 0, 1, 2])
        
        transition_matrix = strategy.calculate_transition_matrix(regime_labels)
        
        assert isinstance(transition_matrix, np.ndarray)
        assert transition_matrix.shape == (6, 6)  # 6x6 matrix
        assert np.allclose(transition_matrix.sum(axis=1), 1.0, atol=1e-10)  # Rows sum to 1
    
    def test_forecast_regime_returns(self, strategy, sample_asset_data):
        """Test regime-conditional return forecasting"""
        # Create sample regime data
        processed_data = strategy.preprocess_macro_data(sample_asset_data)
        regime_labels, regime_probs = strategy.regime_classification(processed_data)
        transition_matrix = strategy.calculate_transition_matrix(regime_labels)
        
        forecasts = strategy.forecast_regime_returns(
            sample_asset_data, regime_labels, regime_probs, transition_matrix
        )
        
        assert isinstance(forecasts, pd.DataFrame)
        assert len(forecasts) == len(sample_asset_data)
        assert forecasts.shape[1] == len(strategy.etfs)
    
    def test_construct_portfolio_long_only(self, strategy, sample_asset_data):
        """Test long-only portfolio construction"""
        # Create sample forecasts
        forecasts = pd.DataFrame(
            np.random.randn(len(sample_asset_data), len(strategy.etfs)),
            index=sample_asset_data.index,
            columns=strategy.etfs
        )
        
        weights = strategy.construct_portfolio(forecasts, 'long_only', 3)
        
        assert isinstance(weights, pd.DataFrame)
        assert weights.shape == forecasts.shape
        assert np.all(weights >= 0)  # Long-only positions
        assert np.allclose(weights.sum(axis=1), 1.0, atol=1e-10)  # Weights sum to 1
    
    def test_construct_portfolio_long_short(self, strategy, sample_asset_data):
        """Test long-short portfolio construction"""
        forecasts = pd.DataFrame(
            np.random.randn(len(sample_asset_data), len(strategy.etfs)),
            index=sample_asset_data.index,
            columns=strategy.etfs
        )
        
        weights = strategy.construct_portfolio(forecasts, 'long_short', 2)
        
        assert isinstance(weights, pd.DataFrame)
        assert weights.shape == forecasts.shape
        # Long-short can have negative weights
        assert np.allclose(weights.sum(axis=1), 0.0, atol=1e-10)  # Net zero exposure
    
    def test_construct_portfolio_mixed(self, strategy, sample_asset_data):
        """Test mixed portfolio construction"""
        forecasts = pd.DataFrame(
            np.random.randn(len(sample_asset_data), len(strategy.etfs)),
            index=sample_asset_data.index,
            columns=strategy.etfs
        )
        
        # Set regime classifications for mixed strategy
        strategy.regime_classifications = np.random.randint(0, 6, len(sample_asset_data))
        
        weights = strategy.construct_portfolio(forecasts, 'mixed', 2)
        
        assert isinstance(weights, pd.DataFrame)
        assert weights.shape == forecasts.shape
    
    @patch('tactical_asset_allocation_regime.Fred')
    @patch('tactical_asset_allocation_regime.xbbg')
    def test_backtest_strategy(self, mock_xbbg, mock_fred, strategy):
        """Test complete backtest"""
        # Mock data fetching
        mock_fred_instance = Mock()
        mock_fred_instance.get_series.return_value = pd.Series(
            np.random.randn(48), 
            index=pd.date_range('2020-01-01', periods=48, freq='M')
        )
        mock_fred.return_value = mock_fred_instance
        
        mock_xbbg.bdh.return_value = pd.Series(
            np.random.uniform(100, 200, 48),
            index=pd.date_range('2020-01-01', periods=48, freq='M')
        )
        
        results = strategy.backtest_strategy('2020-01-01', '2023-12-31')
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check that all strategies have required metrics
        required_metrics = ['total_return', 'annual_return', 'volatility', 
                          'sharpe_ratio', 'max_drawdown', 'win_rate', 'returns']
        
        for strategy_name, metrics in results.items():
            assert isinstance(strategy_name, str)
            assert isinstance(metrics, dict)
            for metric in required_metrics:
                assert metric in metrics
    
    def test_error_handling_no_fred_key(self):
        """Test error handling when no FRED API key is provided"""
        strategy = TacticalAssetAllocationRegime()
        
        with pytest.raises(ValueError, match="FRED API key required"):
            strategy.fetch_macroeconomic_data()
    
    def test_regime_probability_calculation(self, strategy):
        """Test regime probability calculation"""
        # Create sample data
        data = np.random.randn(100, 5)
        kmeans_l2 = Mock()
        kmeans_l2.transform.return_value = np.random.rand(100, 2)
        
        kmeans_cosine = Mock()
        kmeans_cosine.transform.return_value = np.random.rand(80, 5)
        
        typical_mask = np.random.choice([True, False], 100)
        
        regime_probs = strategy._calculate_regime_probabilities(
            data, kmeans_l2, kmeans_cosine, typical_mask
        )
        
        assert isinstance(regime_probs, np.ndarray)
        assert regime_probs.shape == (100, 6)
        assert np.allclose(regime_probs.sum(axis=1), 1.0, atol=1e-10)

if __name__ == "__main__":
    pytest.main([__file__]) 