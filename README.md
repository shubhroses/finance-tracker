# Finance Tracker

A comprehensive stock analysis and portfolio management tool built with Streamlit.

## Features

- 📊 Single Stock Analysis
- 🔄 Stock Comparison
- 💼 Portfolio Analysis
- 📈 Technical Indicators
- 📰 News & Sentiment Analysis

## Quick Deploy

### Deploy on Streamlit Cloud (Recommended)

1. Fork this repository to your GitHub account
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select this repository and branch
6. Select `app.py` as the main file
7. Click "Deploy"

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd finance-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Select an analysis type from the sidebar (Stock Analysis, Compare Stocks, or Portfolio Analysis)
2. For Stock Analysis:
   - Enter a stock ticker (e.g., AAPL)
   - Choose time period
   - Explore different tabs for detailed analysis
3. For Stock Comparison:
   - Enter multiple tickers
   - Compare performance and metrics
4. For Portfolio Analysis:
   - Enter your holdings
   - View portfolio metrics and allocation

## Project Structure

```
finance-tracker/
├── app.py                  # Main application file
├── requirements.txt        # Project dependencies
├── README.md              # Project documentation
└── components/            # Application components
    ├── __init__.py
    ├── sidebar.py         # Sidebar component
    ├── overview.py        # Company overview component
    ├── charts.py         # Price charts component
    ├── technical.py      # Technical analysis component
    ├── financials.py     # Financial metrics component
    ├── comparison.py     # Stock comparison component
    ├── portfolio.py      # Portfolio analysis component
    └── news.py           # News and sentiment component
```

## Dependencies

- streamlit>=1.28.0
- yfinance>=0.2.31
- pandas>=2.1.0
- numpy>=1.24.0
- plotly>=5.18.0
- python-dateutil>=2.8.2

## Data Sources

This application uses the Yahoo Finance API (via yfinance) to fetch real-time and historical financial data. Please note that API limitations may affect data retrieval.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 