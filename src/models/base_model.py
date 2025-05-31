from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

@dataclass
class OptionParams:
    S: float
    K: float
    T: float
    r: float
    sigma: float
    div_yield: float = 0.0
    is_call: bool = True
class BaseOptionModel(ABC):
    
    def __init__(self, name: str):
        self.name = name
        self._validate_name()
    
    def _validate_name(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Model name must be a non-empty string")

    @abstractmethod
    def price(self, params: OptionParams) -> float:
        """Calculate the option price"""
        pass

    @abstractmethod
    def greeks(self, params: OptionParams) -> Dict[str, float]:
        """Calculate option Greeks"""
        pass

    def _validate_params(self, params: OptionParams):
        """Validate option parameters"""
        if params.S <= 0:
            raise ValueError("Stock price must be positive")
        if params.K <= 0:
            raise ValueError("Strike price must be positive")
        if params.T <= 0:
            raise ValueError("Time to maturity must be positive")
        if params.sigma <= 0:
            raise ValueError("Volatility must be positive")
        if params.r < 0:
            raise ValueError("Risk-free rate cannot be negative")
        if params.div_yield < 0:
            raise ValueError("Dividend yield cannot be negative")

    def _calculate_d1_d2(self, params: OptionParams) -> Tuple[float, float]:
        """Calculate d1 and d2 for BSM type formulas"""
        d1 = ((np.log(params.S / params.K) + 
               (params.r - params.div_yield + 0.5 * params.sigma ** 2) * params.T) / 
               (params.sigma * np.sqrt(params.T)))
        d2 = d1 - params.sigma * np.sqrt(params.T)
        return d1, d2

    def implied_volatility(self, market_price: float, params: OptionParams, 
                         tolerance: float = 1e-5, max_iter: int = 100) -> float:
        """Calculate IV using Newton-Raphson method"""
        sigma = 0.5
        for i in range(max_iter):
            params.sigma = sigma
            price = self.price(params)
            diff = price - market_price
            
            if abs(diff) < tolerance:
                return sigma
                
            vega = self.greeks(params)['vega']
            if abs(vega) < 1e-10:
                raise ValueError("Vega too close to zero, cannot compute implied volatility")
                
            sigma = sigma - diff / vega
            
            if sigma <= 0:
                sigma = 0.0001
                
        raise ValueError(f"Implied volatility did not converge after {max_iter} iterations")

    def _finite_difference_greeks(self, params: OptionParams, 
                                delta_S: float = 0.01, 
                                delta_t: float = 1/365) -> Dict[str, float]:
        """Calculate Greeks using finite difference method"""
        original_price = self.price(params)
        
        # Delta
        params_up = OptionParams(**params.__dict__)
        params_up.S += delta_S
        params_down = OptionParams(**params.__dict__)
        params_down.S -= delta_S
        delta = (self.price(params_up) - self.price(params_down)) / (2 * delta_S)
        
        # Gamma
        gamma = (self.price(params_up) - 2 * original_price + self.price(params_down)) / (delta_S ** 2)
        
        # Theta
        params_t = OptionParams(**params.__dict__)
        params_t.T -= delta_t
        theta = -(self.price(params_t) - original_price) / delta_t
        
        # Vega
        params_vol_up = OptionParams(**params.__dict__)
        params_vol_up.sigma += 0.01
        vega = (self.price(params_vol_up) - original_price) / 0.01
        
        # Rho
        params_r_up = OptionParams(**params.__dict__)
        params_r_up.r += 0.01
        rho = (self.price(params_r_up) - original_price) / 0.01
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        } 