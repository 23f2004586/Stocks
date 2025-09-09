import os
import shutil
from datetime import datetime
import numpy as np
import pandas as pd
from nsepython import nse_get_top_gainers, nse_fetch_history # pip install nsepython

# Fetch top 50 gainers as the base dataset
data = nse_get_top_gainers()
df = pd.DataFrame(data)
df = df.head(50)

# Current datetime string for timestamping
now = datetime.now().strftime('%a %b %d %H:%M:%S IST %Y')

# Define period for historical data (example: last 30 days)
start_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

def calculate_metrics(symbol):
    try:
        hist = nse_fetch_history(symbol=symbol, start=start_date, end=end_date)
        if hist.empty:
            return None
        close_prices = hist['Close Price'].values
        returns = np.diff(close_prices) / close_prices[:-1]

        profit_loss = close_prices[-1] - close_prices[0]
        win_rate = np.sum(returns > 0) / len(returns) * 100 if len(returns) > 0 else 0
        peak = np.maximum.accumulate(close_prices)
        drawdowns = peak - close_prices
        max_drawdown = np.max(drawdowns)
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) != 0 else 0

        return profit_loss, win_rate, max_drawdown, sharpe_ratio
    except Exception:
        return None

# Prepare README content with full metrics table
lines = [
    "# Top 50 Performing Indian Stocks with Metrics\n\n",
    f"*Last updated on: {now}*\n\n",
    "| Stock Symbol | Profit/Loss (INR) | Win Rate (%) | Max Drawdown (INR) | Sharpe Ratio |\n",
    "| ------------ | ----------------- | ------------ | ------------------ | ------------ |\n"
]

for idx, row in df.iterrows():
    metrics = calculate_metrics(row['symbol'])
    if metrics:
        profit_loss, win_rate, max_drawdown, sharpe_ratio = metrics
        lines.append(f"| {row['symbol']} | {profit_loss:.2f} | {win_rate:.2f} | {max_drawdown:.2f} | {sharpe_ratio:.2f} |\n")
    else:
        lines.append(f"| {row['symbol']} | N/A | N/A | N/A | N/A |\n")

# Archive previous README.md if exists
if os.path.exists("README.md"):
    if not os.path.exists("history"):
        os.makedirs("history")
    shutil.copy(
        "README.md",
        f"history/README_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )

# Write updated README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.writelines(lines)
