import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import norm
import yfinance as yf
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import minimize
import warnings


class OptionsPricer:
    def __init__(self):
        self.tooltips = {
            'delta': 'Rate of change of option price with respect to underlying price',
            'gamma': 'Rate of change of delta with respect to underlying price',
            'theta': 'Rate of change of option price with respect to time',
            'vega': 'Rate of change of option price with respect to volatility',
            'rho': 'Rate of change of option price with respect to interest rate'
        }

    def black_scholes(self, S, K, T, r, sigma, option_type='call'):
        """Calculate option price using Black-Scholes formula"""
        try:
            if T <= 0:
                raise ValueError("Time to expiry must be positive")
            if sigma <= 0:
                raise ValueError("Volatility must be positive")
            if S <= 0 or K <= 0:
                raise ValueError("Stock price and strike price must be positive")

            d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            if option_type.lower() == 'call':
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

            return price
        except Exception as e:
            st.error(f"Error in Black-Scholes calculation: {str(e)}")
            return None

    def calculate_greeks(self, S, K, T, r, sigma, option_type='call', delta_S=0.01):
        """Calculate option Greeks including Rho"""
        try:
            # Original Greeks
            greeks = {
                'delta': (self.black_scholes(S + delta_S, K, T, r, sigma, option_type) -
                          self.black_scholes(S - delta_S, K, T, r, sigma, option_type)) / (2 * delta_S),

                'gamma': (self.black_scholes(S + delta_S, K, T, r, sigma, option_type) -
                          2 * self.black_scholes(S, K, T, r, sigma, option_type) +
                          self.black_scholes(S - delta_S, K, T, r, sigma, option_type)) / (delta_S ** 2),

                'theta': (self.black_scholes(S, K, T - 1 / 365, r, sigma, option_type) -
                          self.black_scholes(S, K, T, r, sigma, option_type)) / (1 / 365),

                'vega': (self.black_scholes(S, K, T, r, sigma + 0.01, option_type) -
                         self.black_scholes(S, K, T, r, sigma, option_type)) / 0.01,

                'rho': (self.black_scholes(S, K, T, r + 0.01, sigma, option_type) -
                        self.black_scholes(S, K, T, r, sigma, option_type)) / 0.01
            }
            return greeks
        except Exception as e:
            st.error(f"Error calculating Greeks: {str(e)}")
            return None

    def monte_carlo_price(self, S, K, T, r, sigma, option_type='call', paths=10000):
        """Monte Carlo simulation for path-dependent options"""
        try:
            dt = 1 / 252  # Daily steps
            steps = int(T * 252)

            # Generate paths
            Z = np.random.standard_normal((paths, steps))
            S_paths = S * np.exp(np.cumsum((r - 0.5 * sigma ** 2) * dt +
                                           sigma * np.sqrt(dt) * Z, axis=1))

            # Insert initial stock price
            S_paths = np.insert(S_paths, 0, S, axis=1)

            # Calculate payoffs
            if option_type.lower() == 'call':
                payoffs = np.maximum(S_paths[:, -1] - K, 0)
            else:
                payoffs = np.maximum(K - S_paths[:, -1], 0)

            # Discount payoffs
            option_price = np.exp(-r * T) * np.mean(payoffs)

            return option_price, S_paths
        except Exception as e:
            st.error(f"Error in Monte Carlo simulation: {str(e)}")
            return None, None

    def heston_model(self, S, K, T, r, v0, kappa, theta, sigma, rho, option_type='call'):
        """Heston stochastic volatility model implementation"""
        try:
            dt = 1 / 252
            steps = int(T * 252)
            paths = 10000

            # Generate correlated Brownian motions
            Z1 = np.random.standard_normal((paths, steps))
            Z2 = rho * Z1 + np.sqrt(1 - rho ** 2) * np.random.standard_normal((paths, steps))

            # Initialize arrays
            S_paths = np.zeros((paths, steps + 1))
            v_paths = np.zeros((paths, steps + 1))

            S_paths[:, 0] = S
            v_paths[:, 0] = v0

            # Simulate paths
            for t in range(steps):
                S_paths[:, t + 1] = S_paths[:, t] * np.exp((r - 0.5 * v_paths[:, t]) * dt +
                                                           np.sqrt(v_paths[:, t] * dt) * Z1[:, t])

                v_paths[:, t + 1] = np.maximum(v_paths[:, t] + kappa * (theta - v_paths[:, t]) * dt +
                                               sigma * np.sqrt(v_paths[:, t] * dt) * Z2[:, t], 0)

            # Calculate payoffs
            if option_type.lower() == 'call':
                payoffs = np.maximum(S_paths[:, -1] - K, 0)
            else:
                payoffs = np.maximum(K - S_paths[:, -1], 0)

            option_price = np.exp(-r * T) * np.mean(payoffs)

            return option_price, S_paths, v_paths
        except Exception as e:
            st.error(f"Error in Heston model calculation: {str(e)}")
            return None, None, None

    def plot_greek_sensitivity(self, S, K, T, r, sigma, option_type='call'):
        """Enhanced plot sensitivity analysis of Greeks including Rho"""
        fig = make_subplots(rows=3, cols=2, subplot_titles=('Delta', 'Gamma', 'Theta', 'Vega', 'Rho', 'Price'))

        # Generate range of stock prices
        stock_prices = np.linspace(S * 0.8, S * 1.2, 100)

        # Calculate Greeks and price for each stock price
        results = {'delta': [], 'gamma': [], 'theta': [], 'vega': [], 'rho': [], 'price': []}

        for price in stock_prices:
            greeks = self.calculate_greeks(price, K, T, r, sigma, option_type)
            price_val = self.black_scholes(price, K, T, r, sigma, option_type)

            for key in results.keys():
                if key != 'price':
                    results[key].append(greeks[key])
                else:
                    results[key].append(price_val)

        # Add traces
        fig.add_trace(go.Scatter(x=stock_prices, y=results['delta'], name='Delta'), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_prices, y=results['gamma'], name='Gamma'), row=1, col=2)
        fig.add_trace(go.Scatter(x=stock_prices, y=results['theta'], name='Theta'), row=2, col=1)
        fig.add_trace(go.Scatter(x=stock_prices, y=results['vega'], name='Vega'), row=2, col=2)
        fig.add_trace(go.Scatter(x=stock_prices, y=results['rho'], name='Rho'), row=3, col=1)
        fig.add_trace(go.Scatter(x=stock_prices, y=results['price'], name='Price'), row=3, col=2)

        fig.update_layout(height=1000, width=1000, title_text="Option Sensitivities Analysis",
                          showlegend=True)
        return fig


def main():
    st.title('Option Pricing Dashboard v01')

    # Sidebar configuration
    st.sidebar.header('Option Parameters')

    # Model selection
    pricing_model = st.sidebar.selectbox('Pricing Model',
                                         ['Black-Scholes', 'Monte Carlo', 'Heston'])

    # Basic inputs
    ticker = st.sidebar.text_input('Stock Ticker', 'AAPL')
    option_type = st.sidebar.selectbox('Option Type', ['call', 'put'])

    # Get stock price with error handling
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period='1d')['Close'].iloc[-1]
        st.sidebar.write(f'Current Stock Price: ${current_price:.2f}')
    except Exception as e:
        st.error(f'Error fetching price for {ticker}: {str(e)}')
        return

    # Option parameters with tooltips
    with st.sidebar.expander("Option Parameters", expanded=True):
        strike = st.slider('Strike Price',
                           float(current_price * 0.7),
                           float(current_price * 1.3),
                           float(current_price),
                           help="The price at which the option can be exercised")

        days_to_expiry = st.slider('Days to Expiry',
                                   1, 365, 30,
                                   help="Number of days until option expiration")

        volatility = st.slider('Volatility (%)',
                               1, 100, 30,
                               help="Annualized volatility of the underlying asset") / 100

        risk_free_rate = st.slider('Risk-free Rate (%)',
                                   0, 10, 2,
                                   help="Annual risk-free interest rate") / 100

    # Initialize pricer
    pricer = OptionsPricer()
    T = days_to_expiry / 365

    # Model-specific parameters
    if pricing_model == 'Heston':
        with st.sidebar.expander("Heston Model Parameters", expanded=False):
            v0 = st.slider('Initial Variance', 0.01, 1.0, volatility ** 2)
            kappa = st.slider('Mean Reversion Speed', 0.1, 10.0, 2.0)
            theta = st.slider('Long-term Variance', 0.01, 1.0, volatility ** 2)
            sigma_v = st.slider('Volatility of Variance', 0.1, 1.0, 0.3)
            rho = st.slider('Price-Volatility Correlation', -1.0, 1.0, -0.7)

    # Calculate prices and Greeks based on selected model
    if pricing_model == 'Black-Scholes':
        price = pricer.black_scholes(current_price, strike, T, risk_free_rate, volatility, option_type)
        greeks = pricer.calculate_greeks(current_price, strike, T, risk_free_rate, volatility, option_type)
    elif pricing_model == 'Monte Carlo':
        price, paths = pricer.monte_carlo_price(current_price, strike, T, risk_free_rate, volatility, option_type)
        greeks = pricer.calculate_greeks(current_price, strike, T, risk_free_rate, volatility, option_type)
    else:  # Heston
        price, paths, vol_paths = pricer.heston_model(current_price, strike, T, risk_free_rate,
                                                      v0, kappa, theta, sigma_v, rho, option_type)
        greeks = pricer.calculate_greeks(current_price, strike, T, risk_free_rate, volatility, option_type)

    # Display results in an organized layout
    st.header('Option Pricing Results')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Option Price', f'${price:.2f}')
    with col2:
        st.metric('Delta', f'{greeks["delta"]:.4f}',
                  help=pricer.tooltips['delta'])
    with col3:
        st.metric('Gamma', f'{greeks["gamma"]:.4f}',
                  help=pricer.tooltips['gamma'])

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric('Theta', f'{greeks["theta"]:.4f}',
                  help=pricer.tooltips['theta'])
    with col5:
        st.metric('Vega', f'{greeks["vega"]:.4f}',
                  help=pricer.tooltips['vega'])
    with col6:
        st.metric('Rho', f'{greeks["rho"]:.4f}',
                  help=pricer.tooltips['rho'])

    # Display sensitivity analysis
    st.header('Sensitivity Analysis')
    greek_fig = pricer.plot_greek_sensitivity(current_price, strike, T, risk_free_rate, volatility, option_type)
    st.plotly_chart(greek_fig)

    # Add educational content
    with st.expander("Understanding Options Greeks"):
        st.markdown("""
        ### Key Options Greeks Explained
        - **Delta**: Measures the rate of change in option value with respect to the underlying asset's price
        - **Gamma**: Measures the rate of change in delta with respect to the underlying asset's price
        - **Theta**: Measures the rate of change in option value with respect to time (time decay)
        - **Vega**: Measures the rate of change in option value with respect to volatility
        - **Rho**: Measures the rate of change in option value with respect to the risk-free interest rate
        """)


if __name__ == '__main__':
    main()
