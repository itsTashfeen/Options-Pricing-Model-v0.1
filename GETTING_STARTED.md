# Getting Started with Options Pricing Model

## Project Overview
This option pricing model is a comprehensive python application that is meant for me as a passion project. It implements various option pricing methodologies, volatility calculations and risk metrics. I'm always pushing new version of the application and solving any issue requests. Please reach out if you have any comments as I'd love to learn more from everyone using this.

## Project Structure
This is the current project structure, I'm always updating it so it might look a little bit different.
```
Options-Pricing-Model-v0.1/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py        # Base class for option pricing models
│   │   ├── black_scholes.py     # Black-Scholes model implementation
│   │   └── binomial_tree.py     # Binomial tree model implementation
│   ├── utils/
│   │   ├── __init__.py
│   │   └── volatility.py        # Volatility calculation utilities
│   └── app.py                   # Main Streamlit application
├── Getting_Started.md             # Project dependencies
├── README.md                    # Project documentation
└── ROADMAP.md                   # Roadmap to stay on track if I ever used LLMs for some help.
```

## Key Components

### Models (src/models/)
- **base_model.py**: Abstract base class defining the interface for pricing models.
- **black_scholes.py**: Implementation of the BSM
- **binomial_tree.py**: Implementation of the Binomial pricing model

### Utilities (src/utils/)
- **volatility.py**: Contains various volatility calculation methods:
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

### Main Application (src/app.py)
- Streamlit web interface
- Real-time data fetching (please don't break)
- Interactive option pricing
- Volatility analysis
- Greeks visualization

## Setup Instructions

1. **Clone the Repository**
```bash
git clone https://github.com/itsTashfeen/Options-Pricing-Model-v0.1
cd Options-Pricing-Model-v0.1
```

2. **Create a Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Set Up API Keys**
Create a `.streamlit/secrets.toml` file:
```toml
ALPHA_VANTAGE_API_KEY = "your_api_key_here"
```

5. **Run the Application**
```bash
streamlit run src/app.py
```

## Learning path and prereqs (for anyone interested I also have a lot of notes on my website)

### Understanding the Models
- Study Black-Scholes model theory
- Understand Binomial Tree model
- Review the code implementation
- Practice with simple calculations

### Volatility and Utils
- Learn about different volatility measures
- Understand time series analysis
- Study the volatility calculator implementation
- Practice with real market data
