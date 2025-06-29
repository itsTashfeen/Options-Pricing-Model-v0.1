import numpy as np
from typing import List, Optional, Tuple
import pandas as pd
from scipy.stats import norm
from dataclasses import dataclass

@dataclass
class VolatilityParams:
    returns: np.ndarray
    prices: Optional[np.ndarray] = None
    window: int = 252
    decay: float = 0.94

class VolatilityCalculator:

    @staticmethod
    def calculate_returns(prices: np.ndarray, log_returns: bool = True) -> np.ndarray:
        prices = np.asarray(prices)
        returns = np.full(len(prices), np.nan)
        if log_returns:
            returns[1:] = np.log(prices[1:] / prices[:-1])
        else:
            returns[1:] = prices[1:] / prices[:-1] - 1
        return returns

    @staticmethod
    def historical_volatility(params: VolatilityParams) -> float:
        returns = np.asarray(params.returns)
        valid_returns = returns[~np.isnan(returns)]
        if len(valid_returns) < 2:
            raise ValueError("Need at least 2 returns to calculate volatility")
        annualization = np.sqrt(252)
        return float(np.std(valid_returns, ddof=1) * annualization)

    @staticmethod
    def ewma_volatility(params: VolatilityParams) -> np.ndarray:
        returns = np.asarray(params.returns)
        valid_returns = returns[~np.isnan(returns)]
        
        if len(valid_returns) < 2:
            raise ValueError("Need at least 2 returns for EWMA calculation")
        
        variance = np.full(len(returns), np.nan)
        first_valid_idx = np.where(~np.isnan(returns))[0][0]
        variance[first_valid_idx] = returns[first_valid_idx] ** 2
        
        for t in range(first_valid_idx + 1, len(returns)):
            if not np.isnan(returns[t-1]):
                variance[t] = params.decay * variance[t-1] + (1 - params.decay) * returns[t-1] ** 2
        volatility = np.sqrt(variance) * np.sqrt(252)
        return volatility

    @staticmethod
    def garch_volatility(params: VolatilityParams, alpha: float = 0.1, beta: float = 0.8) -> np.ndarray:
        returns = np.asarray(params.returns)
        valid_returns = returns[~np.isnan(returns)]
        
        if len(valid_returns) < 2:
            raise ValueError("Need at least 2 returns for GARCH calculation")
        
        if alpha + beta >= 1:
            raise ValueError("alpha + beta must be less than 1 for stationarity")
        
        variance = np.full(len(returns), np.nan)
        first_valid_idx = np.where(~np.isnan(returns))[0][0]
        initial_var = np.var(valid_returns)
        omega = (1 - alpha - beta) * initial_var
        variance[first_valid_idx] = initial_var
        for t in range(first_valid_idx + 1, len(returns)):
            if not np.isnan(returns[t-1]):
                variance[t] = (omega + 
                             alpha * returns[t-1]**2 + 
                             beta * variance[t-1])
        volatility = np.sqrt(variance) * np.sqrt(252)
        return volatility

    @staticmethod
    def parkinson_volatility(high: np.ndarray, low: np.ndarray, window: int = 252) -> np.ndarray:
        high = np.asarray(high)
        low = np.asarray(low)
        log_hl = np.log(high / low)
        estimator = 1 / (4 * np.log(2)) * log_hl**2
        rolling_var = pd.Series(estimator).rolling(
            window=window,
            min_periods=2
        ).mean()
        volatility = np.sqrt(252 * rolling_var.to_numpy())
        return volatility

    @staticmethod
    def garman_klass_volatility(open_: np.ndarray, high: np.ndarray, 
                              low: np.ndarray, close: np.ndarray, 
                              window: int = 252) -> np.ndarray:
        open_ = np.asarray(open_)
        high = np.asarray(high)
        low = np.asarray(low)
        close = np.asarray(close)
        log_hl = np.log(high / low)
        log_co = np.log(close / open_)
        estimator = 0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2
        rolling_var = pd.Series(estimator).rolling(
            window=window,
            min_periods=2
        ).mean()
        volatility = np.sqrt(252 * rolling_var.to_numpy())
        return volatility

    @staticmethod
    def yang_zhang_volatility(open_: np.ndarray, high: np.ndarray, 
                            low: np.ndarray, close: np.ndarray, 
                            window: int = 252) -> np.ndarray:
        log_ho = np.log(high / open_)
        log_lo = np.log(low / open_)
        log_co = np.log(close / open_)
        rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
        close_to_open = np.log(open_[1:] / close[:-1])
        open_to_close = log_co[1:]
        sigma_sq_open = pd.Series(close_to_open**2).rolling(window=window).mean()
        sigma_sq_close = pd.Series(open_to_close**2).rolling(window=window).mean()
        sigma_sq_rs = pd.Series(rs[1:]).rolling(window=window).mean()
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        sigma_sq = sigma_sq_open + k * sigma_sq_close + (1 - k) * sigma_sq_rs
        return np.sqrt(252 * sigma_sq)

class ImpliedVolatilitySurface:

    def __init__(self, strikes: np.ndarray, maturities: np.ndarray, 
                 spot: float, rates: np.ndarray, market_prices: np.ndarray):
        self.strikes = strikes
        self.maturities = maturities
        self.spot = spot
        self.rates = rates
        self.market_prices = market_prices
        self.iv_surface = None
    
    def _newton_raphson_iv(self, market_price: float, K: float, T: float, 
                          r: float, is_call: bool = True, 
                          max_iter: int = 100, tolerance: float = 1e-5) -> float:
        sigma = 0.5
        for _ in range(max_iter):
            d1 = (np.log(self.spot/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            if is_call:
                price = self.spot*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
            else:
                price = K*np.exp(-r*T)*norm.cdf(-d2) - self.spot*norm.cdf(-d1)
            diff = price - market_price
            if abs(diff) < tolerance:
                return sigma
            vega = self.spot*np.sqrt(T)*norm.pdf(d1)
            sigma = sigma - diff/vega
        raise ValueError("Implied volatility did not converge")
    
    def calculate_surface(self) -> np.ndarray:
        self.iv_surface = np.zeros_like(self.market_prices)
        for i, K in enumerate(self.strikes):
            for j, T in enumerate(self.maturities):
                try:
                    self.iv_surface[i,j] = self._newton_raphson_iv(
                        self.market_prices[i,j], K, T, self.rates[j]
                    )
                except:
                    self.iv_surface[i,j] = np.nan
        return self.iv_surface
    
    def get_smile(self, maturity_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        if self.iv_surface is None:
            self.calculate_surface()
        return self.strikes, self.iv_surface[:, maturity_idx]
    
    def get_term_structure(self, strike_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        if self.iv_surface is None:
            self.calculate_surface()
        return self.maturities, self.iv_surface[strike_idx, :]
    
    def interpolate(self, strike: float, maturity: float) -> float:
        if self.iv_surface is None:
            self.calculate_surface()
            
        i = np.searchsorted(self.strikes, strike)
        j = np.searchsorted(self.maturities, maturity)
        
        if i == 0 or i == len(self.strikes) or j == 0 or j == len(self.maturities):
            raise ValueError("Strike or maturity out of bounds")
            
        x = (strike - self.strikes[i-1]) / (self.strikes[i] - self.strikes[i-1])
        y = (maturity - self.maturities[j-1]) / (self.maturities[j] - self.maturities[j-1])
        
        v1 = self.iv_surface[i-1,j-1]
        v2 = self.iv_surface[i,j-1]
        v3 = self.iv_surface[i-1,j]
        v4 = self.iv_surface[i,j]
        
        return ((1-x)*(1-y)*v1 + x*(1-y)*v2 + 
                (1-x)*y*v3 + x*y*v4) 