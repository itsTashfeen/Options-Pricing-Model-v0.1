# Advanced Options Pricing Calculator

A sophisticated options pricing and analysis tool that implements multiple pricing models and advanced volatility calculations.

## Features

### Pricing Models
- Black-Scholes Model
- Binomial Tree Model (European & American Options)
- Support for dividends and early exercise
- Comprehensive Greeks calculations

### Volatility Analysis
- Multiple volatility calculation methods:
  - Historical Volatility
  - EWMA (Exponentially Weighted Moving Average)
  - GARCH(1,1)
  - Parkinson Volatility
  - Garman-Klass Volatility
- Volatility surface visualization
- Term structure analysis

### Risk Analytics
- Real-time Greeks calculation and visualization
- Sensitivity analysis
- Model comparison
- Interactive visualizations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Options-Pricing-Model-v0.1.git
cd Options-Pricing-Model-v0.1
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run src/app.py
```

The application will open in your default web browser. You can:
1. Enter a stock ticker to get real-time price data
2. Adjust option parameters (strike, expiry, volatility, etc.)
3. Choose between different pricing models
4. Analyze Greeks and volatility measures
5. Compare results across models

## Project Structure

```
Options-Pricing-Model-v0.1/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── black_scholes.py
│   │   └── binomial_tree.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── volatility.py
│   └── app.py
├── tests/
├── requirements.txt
├── README.md
└── ROADMAP.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Development

See [ROADMAP.md](ROADMAP.md) for planned features and enhancements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Black-Scholes option pricing model
- Cox-Ross-Rubinstein binomial model
- Various volatility calculation methods from academic literature 