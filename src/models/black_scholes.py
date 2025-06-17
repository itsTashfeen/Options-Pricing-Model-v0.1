import numpy as np
from scipy.stats import norm
from .base_model import BaseOptionModel, OptionParams
from typing import Dict

class BlackScholesModel(BaseOptionModel):
    
    def __init__(self):
        super().__init__("Black-Scholes")

    def price(self, params: OptionParams) -> float:
        self._validate_params(params)
        d1, d2 = self._calculate_d1_d2(params)
        
        if params.is_call:
            price = (params.S * np.exp(-params.div_yield * params.T) * norm.cdf(d1) - 
                    params.K * np.exp(-params.r * params.T) * norm.cdf(d2))
        
        else:
            price = (params.K * np.exp(-params.r * params.T) * norm.cdf(-d2) - 
                    params.S * np.exp(-params.div_yield * params.T) * norm.cdf(-d1))
        
        return price

    def greeks(self, params: OptionParams) -> Dict[str, float]:
        self._validate_params(params)
        d1, d2 = self._calculate_d1_d2(params)
        S = params.S
        K = params.K
        T = params.T
        r = params.r
        sigma = params.sigma
        q = params.div_yield
        exp_qt = np.exp(-q * T)
        exp_rt = np.exp(-r * T)
        sqrt_T = np.sqrt(T)
        
        if params.is_call:
            delta = exp_qt * norm.cdf(d1)
            theta = (-S * exp_qt * norm.pdf(d1) * sigma / (2 * sqrt_T) -
                    r * K * exp_rt * norm.cdf(d2) +
                    q * S * exp_qt * norm.cdf(d1))
        else:
            delta = -exp_qt * norm.cdf(-d1)
            theta = (-S * exp_qt * norm.pdf(d1) * sigma / (2 * sqrt_T) +
                    r * K * exp_rt * norm.cdf(-d2) -
                    q * S * exp_qt * norm.cdf(-d1))
        gamma = exp_qt * norm.pdf(d1) / (S * sigma * sqrt_T)
        vega = S * exp_qt * sqrt_T * norm.pdf(d1)
        rho = K * T * exp_rt * (norm.cdf(d2) if params.is_call else -norm.cdf(-d2))
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        } 