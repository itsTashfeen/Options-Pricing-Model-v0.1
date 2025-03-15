import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta

from models.black_scholes import BlackScholesModel
from models.binomial_tree import BinomialTreeModel
from models.base_model import OptionParams
from utils.volatility import VolatilityCalculator, VolatilityParams, ImpliedVolatilitySurface

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"] if "ALPHA_VANTAGE_API_KEY" in st.secrets else ""

class OptionsCalculator:
    def __init__(self):
        self.models = {
            'Black-Scholes': BlackScholesModel(),
            'Binomial Tree (European)': BinomialTreeModel(steps=100, american=False),
            'Binomial Tree (American)': BinomialTreeModel(steps=100, american=True)
        }
        self.vol_calculator = VolatilityCalculator()
        
    def calculate_all_greeks(self, params: OptionParams, model_name: str) -> dict:
        """Calculate option price and Greeks using specified model"""
        model = self.models[model_name]
        price = model.price(params)
        greeks = model.greeks(params)
        return {'price': price, **greeks}

def fetch_stock_data(ticker: str, days: int = 252) -> tuple:
    """
    Fetch stock data using Alpha Vantage API
    Returns: (current_price, historical_data)
    """
    if not ALPHA_VANTAGE_API_KEY:
        st.error("Alpha Vantage API key is missing. Please set it in your Streamlit secrets.")
        st.info("You can get a free API key from: https://www.alphavantage.co/support/#api-key")
        raise ValueError("Alpha Vantage API key is required")

    try:
        # Fetch daily data
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "Error Message" in data:
            raise ValueError(f"Error from Alpha Vantage: {data['Error Message']}")
        
        if "Time Series (Daily)" not in data:
            raise ValueError(f"No data available for {ticker}")

        # Convert to DataFrame
        hist_data = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        hist_data.index = pd.to_datetime(hist_data.index)
        hist_data = hist_data.sort_index()
        
        # Rename columns
        hist_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        hist_data = hist_data.astype(float)
        
        # Get only the required number of days
        start_date = datetime.now() - timedelta(days=days)
        hist_data = hist_data[hist_data.index >= start_date]
        
        if hist_data.empty:
            raise ValueError(f"No recent data available for {ticker}")
        
        current_price = float(hist_data['Close'].iloc[-1])
        return current_price, hist_data

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error while fetching data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error fetching data for {ticker}: {str(e)}")

def calculate_volatility_measures(calculator: VolatilityCalculator, hist_data: pd.DataFrame, window: int) -> tuple:
    """Calculate various volatility measures with error handling"""
    try:
        # Ensure we have enough data
        if len(hist_data) < window:
            raise ValueError(f"Need at least {window} days of data for volatility calculations")
        
        # Calculate returns and create parameters
        returns = calculator.calculate_returns(hist_data['Close'].values)
        vol_params = VolatilityParams(
            returns=returns,
            prices=hist_data['Close'].values,
            window=window
        )
        
        # Calculate historical volatility (scalar)
        hist_vol = calculator.historical_volatility(vol_params)
        
        # Calculate time series volatilities
        ewma_series = calculator.ewma_volatility(vol_params)
        garch_series = calculator.garch_volatility(vol_params)
        park_series = calculator.parkinson_volatility(
            hist_data['High'].values,
            hist_data['Low'].values,
            window=window
        )
        gk_series = calculator.garman_klass_volatility(
            hist_data['Open'].values,
            hist_data['High'].values,
            hist_data['Low'].values,
            hist_data['Close'].values,
            window=window
        )
        
        # Get the most recent values for the summary table
        def get_last_valid(series):
            if isinstance(series, np.ndarray):
                # Remove any NaN values from the end
                valid_indices = ~np.isnan(series)
                if not np.any(valid_indices):
                    return None
                last_valid_idx = np.where(valid_indices)[0][-1]
                return float(series[last_valid_idx])
            return None
        
        return (
            hist_vol,
            get_last_valid(ewma_series),
            get_last_valid(garch_series),
            get_last_valid(park_series),
            get_last_valid(gk_series)
        ), (ewma_series, garch_series, park_series, gk_series)
        
    except Exception as e:
        st.error(f"Detailed error in volatility calculation: {str(e)}")
        raise ValueError(f"Error calculating volatility measures: {str(e)}")

def main():
    st.set_page_config(page_title="Advanced Options Calculator", layout="wide")
    
    st.title("Advanced Options Pricing Calculator")
    st.markdown("""
    This application provides advanced options pricing capabilities using multiple models
    and sophisticated volatility calculations.
    """)
    
    # Initialize calculator
    calculator = OptionsCalculator()
    
    # Sidebar inputs
    with st.sidebar:
        st.header("Option Parameters")
        
        # Stock information
        ticker = st.text_input("Stock Ticker", "AAPL")
        
        try:
            current_price, hist_data = fetch_stock_data(ticker)
            st.success(f"Current Stock Price: ${current_price:.2f}")
        except Exception as e:
            st.error(str(e))
            current_price = 100.0  # Default value
            hist_data = None
        
        # Basic parameters
        strike = st.number_input("Strike Price", min_value=0.01, value=float(current_price))
        days = st.slider("Days to Expiry", min_value=1, max_value=365, value=30)
        volatility = st.slider("Volatility (%)", min_value=1, max_value=100, value=30) / 100
        risk_free = st.slider("Risk-free Rate (%)", min_value=0, max_value=10, value=2) / 100
        dividend = st.slider("Dividend Yield (%)", min_value=0, max_value=10, value=0) / 100
        
        # Model selection
        model_name = st.selectbox("Pricing Model", list(calculator.models.keys()))
        option_type = st.selectbox("Option Type", ["call", "put"])
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            if "Binomial" in model_name:
                steps = st.slider("Tree Steps", min_value=10, max_value=1000, value=100)
                calculator.models[model_name].steps = steps
            
            vol_window = st.slider("Volatility Window (days)", min_value=5, max_value=252, value=30)
    
    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["Option Pricing", "Volatility Analysis", "Greeks Analysis"])
    
    # Option parameters
    params = OptionParams(
        S=current_price,
        K=strike,
        T=days/365,
        r=risk_free,
        sigma=volatility,
        div_yield=dividend,
        is_call=(option_type == "call")
    )
    
    # Tab 1: Option Pricing
    with tab1:
        st.header("Option Pricing Results")
        
        try:
            # Calculate results
            results = calculator.calculate_all_greeks(params, model_name)
            
            # Display results in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Option Price", f"${results['price']:.2f}")
            with col2:
                st.metric("Delta", f"{results['delta']:.4f}")
            with col3:
                st.metric("Gamma", f"{results['gamma']:.4f}")
                
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric("Theta", f"{results['theta']:.4f}")
            with col5:
                st.metric("Vega", f"{results['vega']:.4f}")
            with col6:
                st.metric("Rho", f"{results['rho']:.4f}")
            
            # Model comparison
            st.subheader("Model Comparison")
            comparison_df = pd.DataFrame(columns=['Model', 'Price', 'Delta', 'Gamma', 'Theta', 'Vega', 'Rho'])
            
            for model_name in calculator.models.keys():
                results = calculator.calculate_all_greeks(params, model_name)
                comparison_df.loc[len(comparison_df)] = [
                    model_name, 
                    results['price'],
                    results['delta'],
                    results['gamma'],
                    results['theta'],
                    results['vega'],
                    results['rho']
                ]
            
            st.dataframe(comparison_df.style.format({
                'Price': '${:.2f}',
                'Delta': '{:.4f}',
                'Gamma': '{:.4f}',
                'Theta': '{:.4f}',
                'Vega': '{:.4f}',
                'Rho': '{:.4f}'
            }))
        except Exception as e:
            st.error(f"Error calculating option prices: {str(e)}")
    
    # Tab 2: Volatility Analysis
    with tab2:
        st.header("Volatility Analysis")
        
        if hist_data is not None and len(hist_data) >= 2:
            try:
                # Calculate volatility measures
                current_vols, vol_series = calculate_volatility_measures(
                    calculator.vol_calculator, hist_data, vol_window
                )
                hist_vol, ewma_vol, garch_vol, park_vol, gk_vol = current_vols
                ewma_series, garch_series, park_series, gk_series = vol_series
                
                # Create volatility comparison plot
                fig = go.Figure()
                
                # Only add traces for non-None values and series
                dates = hist_data.index
                
                if ewma_series is not None:
                    valid_indices = ~np.isnan(ewma_series)
                    if np.any(valid_indices):
                        fig.add_trace(go.Scatter(
                            x=dates[valid_indices],
                            y=ewma_series[valid_indices],
                            name='EWMA'
                        ))
                
                if garch_series is not None:
                    valid_indices = ~np.isnan(garch_series)
                    if np.any(valid_indices):
                        fig.add_trace(go.Scatter(
                            x=dates[valid_indices],
                            y=garch_series[valid_indices],
                            name='GARCH(1,1)'
                        ))
                
                if park_series is not None:
                    valid_indices = ~np.isnan(park_series)
                    if np.any(valid_indices):
                        fig.add_trace(go.Scatter(
                            x=dates[valid_indices],
                            y=park_series[valid_indices],
                            name='Parkinson'
                        ))
                
                if gk_series is not None:
                    valid_indices = ~np.isnan(gk_series)
                    if np.any(valid_indices):
                        fig.add_trace(go.Scatter(
                            x=dates[valid_indices],
                            y=gk_series[valid_indices],
                            name='Garman-Klass'
                        ))
                
                fig.update_layout(
                    title=f'Volatility Measures for {ticker}',
                    xaxis_title='Date',
                    yaxis_title='Annualized Volatility',
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display current volatility measures
                st.subheader("Current Volatility Measures")
                measures = []
                values = []
                
                if hist_vol is not None:
                    measures.append('Historical')
                    values.append(hist_vol)
                if ewma_vol is not None:
                    measures.append('EWMA')
                    values.append(ewma_vol)
                if garch_vol is not None:
                    measures.append('GARCH(1,1)')
                    values.append(garch_vol)
                if park_vol is not None:
                    measures.append('Parkinson')
                    values.append(park_vol)
                if gk_vol is not None:
                    measures.append('Garman-Klass')
                    values.append(gk_vol)
                
                if measures and values:
                    vol_df = pd.DataFrame({
                        'Measure': measures,
                        'Value': values
                    })
                    
                    st.dataframe(vol_df.style.format({
                        'Value': '{:.2%}'
                    }))
                else:
                    st.warning("No valid volatility measures could be calculated with the current data")
                
            except Exception as e:
                st.error(f"Error calculating volatility measures: {str(e)}")
        else:
            st.warning(f"Insufficient historical data available for {ticker} to calculate volatility measures. Please try a different ticker or ensure market data is available.")
    
    # Tab 3: Greeks Analysis
    with tab3:
        st.header("Greeks Analysis")
        
        try:
            # Create price range for analysis
            price_range = np.linspace(current_price * 0.5, current_price * 1.5, 100)
            
            # Calculate Greeks across price range
            results = {
                'price': [], 'delta': [], 'gamma': [], 'theta': [], 'vega': [], 'rho': []
            }
            
            for price in price_range:
                params.S = price
                calcs = calculator.calculate_all_greeks(params, model_name)
                for key in results:
                    results[key].append(calcs[key] if key != 'price' else calcs['price'])
            
            # Create subplots for Greeks
            fig = make_subplots(rows=3, cols=2,
                              subplot_titles=('Price', 'Delta', 'Gamma', 'Theta', 'Vega', 'Rho'))
            
            # Add traces
            fig.add_trace(go.Scatter(x=price_range, y=results['price'], name='Price'),
                         row=1, col=1)
            fig.add_trace(go.Scatter(x=price_range, y=results['delta'], name='Delta'),
                         row=1, col=2)
            fig.add_trace(go.Scatter(x=price_range, y=results['gamma'], name='Gamma'),
                         row=2, col=1)
            fig.add_trace(go.Scatter(x=price_range, y=results['theta'], name='Theta'),
                         row=2, col=2)
            fig.add_trace(go.Scatter(x=price_range, y=results['vega'], name='Vega'),
                         row=3, col=1)
            fig.add_trace(go.Scatter(x=price_range, y=results['rho'], name='Rho'),
                         row=3, col=2)
            
            fig.update_layout(height=800, title_text=f"Greeks Analysis ({model_name})")
            st.plotly_chart(fig, use_container_width=True)
            
            # Add educational content
            with st.expander("Understanding the Greeks"):
                st.markdown("""
                ### Key Options Greeks Explained
                
                - **Delta (Δ)**: Measures the rate of change in option value with respect to the underlying asset's price
                - **Gamma (Γ)**: Measures the rate of change in delta with respect to the underlying asset's price
                - **Theta (Θ)**: Measures the rate of change in option value with respect to time (time decay)
                - **Vega (v)**: Measures the rate of change in option value with respect to volatility
                - **Rho (ρ)**: Measures the rate of change in option value with respect to the risk-free interest rate
                
                ### Interpretation
                
                - A **Delta** of 0.5 means the option price will change by $0.50 for every $1 change in the underlying price
                - A **Gamma** of 0.1 means the delta will change by 0.1 for every $1 change in the underlying price
                - A **Theta** of -0.1 means the option loses $0.10 in value each day, all else being equal
                - A **Vega** of 0.2 means the option value changes by $0.20 for every 1% change in volatility
                - A **Rho** of 0.3 means the option value changes by $0.30 for every 1% change in interest rates
                """)
        except Exception as e:
            st.error(f"Error calculating Greeks: {str(e)}")

if __name__ == "__main__":
    main() 