import numpy as np
from typing import Dict, List, Tuple
from .base_model import BaseOptionModel, OptionParams

class BinomialTreeModel(BaseOptionModel):
    """Binomial Tree option pricing model with support for both European and American options"""
    
    def __init__(self, steps: int = 100, american: bool = False):
        """
        Initialize Binomial Tree model
        
        Parameters:
        -----------
        steps : int
            Number of time steps in the tree
        american : bool
            Whether to price American options (True) or European options (False)
        """
        super().__init__("Binomial Tree")
        self.steps = steps
        self.american = american

    def _build_tree(self, params: OptionParams) -> Tuple[np.ndarray, float, float, float]:
        """Build the binomial price tree"""
        dt = params.T / self.steps
        u = np.exp(params.sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp((params.r - params.div_yield) * dt) - d) / (u - d)
        
        # Initialize stock price tree
        stock_tree = np.zeros((self.steps + 1, self.steps + 1))
        stock_tree[0, 0] = params.S
        
        # Build stock price tree
        for i in range(1, self.steps + 1):
            # Up movements
            for j in range(i+1):
                stock_tree[j, i] = params.S * (u ** (i-j)) * (d ** j)
        
        return stock_tree, p, u, d

    def price(self, params: OptionParams) -> float:
        """
        Calculate option price using the binomial tree method
        
        Parameters:
        -----------
        params : OptionParams
            Option parameters
            
        Returns:
        --------
        float
            Option price
        """
        self._validate_params(params)
        
        # Build the tree
        stock_tree, p, u, d = self._build_tree(params)
        
        # Initialize option value tree
        option_tree = np.zeros((self.steps + 1, self.steps + 1))
        
        # Calculate option payoff at maturity
        if params.is_call:
            option_tree[:, self.steps] = np.maximum(0, stock_tree[:, self.steps] - params.K)
        else:
            option_tree[:, self.steps] = np.maximum(0, params.K - stock_tree[:, self.steps])
        
        # Discount factors
        dt = params.T / self.steps
        df = np.exp(-params.r * dt)
        
        # Backward induction through the tree
        for j in range(self.steps - 1, -1, -1):
            for i in range(j + 1):
                hold_value = df * (p * option_tree[i, j + 1] + (1 - p) * option_tree[i + 1, j + 1])
                
                if self.american:
                    # For American options, check if early exercise is optimal
                    if params.is_call:
                        exercise_value = stock_tree[i, j] - params.K
                    else:
                        exercise_value = params.K - stock_tree[i, j]
                    option_tree[i, j] = max(hold_value, exercise_value)
                else:
                    option_tree[i, j] = hold_value
        
        return option_tree[0, 0]

    def greeks(self, params: OptionParams) -> Dict[str, float]:
        """
        Calculate option Greeks using finite differences
        
        Parameters:
        -----------
        params : OptionParams
            Option parameters
            
        Returns:
        --------
        Dict[str, float]
            Dictionary containing delta, gamma, theta, vega, and rho
        """
        return self._finite_difference_greeks(params)

    def get_price_tree(self, params: OptionParams) -> np.ndarray:
        """
        Get the full price tree for analysis
        
        Parameters:
        -----------
        params : OptionParams
            Option parameters
            
        Returns:
        --------
        np.ndarray
            2D array containing the option prices at each node
        """
        self._validate_params(params)
        return self._build_tree(params)[0]

    def get_early_exercise_boundary(self, params: OptionParams) -> List[float]:
        """
        Calculate the early exercise boundary for American options
        
        Parameters:
        -----------
        params : OptionParams
            Option parameters
            
        Returns:
        --------
        List[float]
            Early exercise prices at each time step
        """
        if not self.american:
            raise ValueError("Early exercise boundary only available for American options")
        
        stock_tree, _, _, _ = self._build_tree(params)
        option_tree = np.zeros_like(stock_tree)
        
        # Calculate option payoff at maturity
        if params.is_call:
            option_tree[:, self.steps] = np.maximum(0, stock_tree[:, self.steps] - params.K)
        else:
            option_tree[:, self.steps] = np.maximum(0, params.K - stock_tree[:, self.steps])
            
        boundary = []
        
        for j in range(self.steps + 1):
            exercise_points = []
            for i in range(j + 1):
                if params.is_call:
                    intrinsic = stock_tree[i, j] - params.K
                else:
                    intrinsic = params.K - stock_tree[i, j]
                    
                if abs(option_tree[i, j] - intrinsic) < 1e-10:
                    exercise_points.append(stock_tree[i, j])
            
            if exercise_points:
                if params.is_call:
                    boundary.append(min(exercise_points))
                else:
                    boundary.append(max(exercise_points))
            else:
                boundary.append(np.nan)
        
        return boundary 