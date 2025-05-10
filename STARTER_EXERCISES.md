# Starter Exercises for Options Pricing Model

This document contains progressive exercises to help you understand both Python programming and options pricing concepts. Start from the beginning and work your way up.

## Part 1: Python Basics

### Exercise 1: Variables and Basic Math
```python
# Create a file named exercise1.py
# Calculate the percentage change between two stock prices

initial_price = 100
final_price = 110

# TODO: Calculate the percentage change
percentage_change = ((final_price - initial_price) / initial_price) * 100

print(f"The percentage change is: {percentage_change}%")
```

### Exercise 2: Lists and Loops
```python
# Create a file named exercise2.py
# Calculate the daily returns for a list of stock prices

stock_prices = [100, 102, 99, 101, 103, 98, 99]

# TODO: Calculate daily returns
daily_returns = []
for i in range(1, len(stock_prices)):
    daily_return = (stock_prices[i] - stock_prices[i-1]) / stock_prices[i-1]
    daily_returns.append(daily_return)

print("Daily returns:", daily_returns)
```

### Exercise 3: Functions
```python
# Create a file named exercise3.py
# Create a function to calculate simple interest

def calculate_simple_interest(principal, rate, time):
    """
    Calculate simple interest
    principal: initial amount
    rate: annual interest rate (as decimal)
    time: time in years
    """
    # TODO: Implement the function
    interest = principal * rate * time
    return interest

# Test the function
principal = 1000
rate = 0.05  # 5%
time = 2     # 2 years

interest = calculate_simple_interest(principal, rate, time)
print(f"Simple interest: ${interest}")
```

## Part 2: Financial Math Basics

### Exercise 4: Present Value
```python
# Create a file named exercise4.py
# Calculate the present value of a future payment

def calculate_present_value(future_value, rate, time):
    """
    Calculate present value
    future_value: future payment amount
    rate: annual interest rate (as decimal)
    time: time in years
    """
    # TODO: Implement the present value formula
    present_value = future_value / (1 + rate)**time
    return present_value

# Test the function
future_value = 1100
rate = 0.05
time = 2

pv = calculate_present_value(future_value, rate, time)
print(f"Present value: ${pv:.2f}")
```

### Exercise 5: Volatility
```python
# Create a file named exercise5.py
# Calculate historical volatility

import numpy as np

def calculate_volatility(prices, trading_days=252):
    """
    Calculate annualized historical volatility
    prices: list of stock prices
    trading_days: number of trading days in a year
    """
    # TODO: 
    # 1. Calculate daily returns
    # 2. Calculate standard deviation
    # 3. Annualize the volatility
    
    returns = np.log(prices[1:] / prices[:-1])
    std_dev = np.std(returns, ddof=1)
    volatility = std_dev * np.sqrt(trading_days)
    
    return volatility

# Test the function
prices = [100, 102, 99, 101, 103, 98, 99, 102, 104, 103]
vol = calculate_volatility(prices)
print(f"Annualized volatility: {vol:.2%}")
```

## Part 3: Options Basics

### Exercise 6: Call Option Payoff
```python
# Create a file named exercise6.py
# Calculate call option payoff at expiration

def calculate_call_payoff(spot_price, strike_price):
    """
    Calculate call option payoff
    spot_price: current stock price
    strike_price: option strike price
    """
    # TODO: Implement the call option payoff formula
    payoff = max(spot_price - strike_price, 0)
    return payoff

# Test the function
spot_prices = [90, 95, 100, 105, 110]
strike_price = 100

print("Call Option Payoffs:")
for spot in spot_prices:
    payoff = calculate_call_payoff(spot, strike_price)
    print(f"Spot Price: ${spot}, Payoff: ${payoff}")
```

### Exercise 7: Put Option Payoff
```python
# Create a file named exercise7.py
# Calculate put option payoff at expiration

def calculate_put_payoff(spot_price, strike_price):
    """
    Calculate put option payoff
    spot_price: current stock price
    strike_price: option strike price
    """
    # TODO: Implement the put option payoff formula
    payoff = max(strike_price - spot_price, 0)
    return payoff

# Test the function
spot_prices = [90, 95, 100, 105, 110]
strike_price = 100

print("Put Option Payoffs:")
for spot in spot_prices:
    payoff = calculate_put_payoff(spot, strike_price)
    print(f"Spot Price: ${spot}, Payoff: ${payoff}")
```

## Part 4: Black-Scholes Basics

### Exercise 8: d1 and d2 Calculations
```python
# Create a file named exercise8.py
# Calculate d1 and d2 for the Black-Scholes formula

import numpy as np
from scipy.stats import norm

def calculate_d1_d2(S, K, T, r, sigma):
    """
    Calculate d1 and d2 for Black-Scholes
    S: spot price
    K: strike price
    T: time to expiration (in years)
    r: risk-free rate
    sigma: volatility
    """
    # TODO: Implement d1 and d2 calculations
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2

# Test the function
S = 100    # Spot price
K = 100    # Strike price
T = 1      # One year
r = 0.05   # 5% risk-free rate
sigma = 0.2 # 20% volatility

d1, d2 = calculate_d1_d2(S, K, T, r, sigma)
print(f"d1: {d1:.4f}")
print(f"d2: {d2:.4f}")
```

### Exercise 9: Simple Black-Scholes
```python
# Create a file named exercise9.py
# Implement a basic Black-Scholes calculator

import numpy as np
from scipy.stats import norm

def black_scholes_call(S, K, T, r, sigma):
    """
    Calculate Black-Scholes call option price
    S: spot price
    K: strike price
    T: time to expiration (in years)
    r: risk-free rate
    sigma: volatility
    """
    # TODO: Implement the Black-Scholes formula
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return call_price

# Test the function
S = 100    # Spot price
K = 100    # Strike price
T = 1      # One year
r = 0.05   # 5% risk-free rate
sigma = 0.2 # 20% volatility

price = black_scholes_call(S, K, T, r, sigma)
print(f"Call option price: ${price:.2f}")
```

## How to Use These Exercises

1. Create a new directory for exercises:
```bash
mkdir python_exercises
cd python_exercises
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install numpy scipy pandas matplotlib
```

4. Create each exercise file and implement the solutions.

5. Run each exercise:
```bash
python exercise1.py
```

## Learning Tips

1. **Type the Code**: Don't copy-paste. Type each exercise manually to build muscle memory.

2. **Experiment**: After completing each exercise, try modifying the parameters and see how the results change.

3. **Understand the Math**: Make sure you understand the financial concepts behind each calculation.

4. **Debug**: If you get errors, read them carefully and try to fix them yourself before seeking help.

5. **Document**: Add comments to explain what each part of your code does.

## Next Steps

After completing these exercises:

1. Study the actual project code in `src/models/` and `src/utils/`
2. Try to implement additional features
3. Write your own test cases
4. Experiment with different parameters
5. Try to create visualizations of the results

Remember: These exercises are just the beginning. The actual project is more complex, but these exercises will give you the foundation you need to understand and work with the full codebase. 