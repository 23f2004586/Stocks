import os
import shutil
from datetime import datetime, date
import time
import numpy as np
import pandas as pd
import finnhub

# Set your API key explicitly here or set as environment variable
api_key = "d32nfrpr01qtm630raegd32nfrpr01qtm630raf0"
finnhub_client = finnhub.Client(api_key=api_key)

now = datetime.now().strftime('%a %b %d %H:%M:%S IST %Y')

def unix_timestamp(dt):
    return int(time.mktime(dt.timetuple()))

def calculate_metrics(symbol):
    try:
        end_dt = date.today()
        start_dt = end_dt - pd.Timedelta(days=30)
        start_ts = unix_timestamp(start_dt)
        end_ts = unix_timestamp(end_dt)

        res = finnhub_client.stock_candles(symbol, 'D', start_ts, end_ts)
        if res['s'] != 'ok' or 'c' not in res or len(res['c']) == 0:
            return None

        close_prices = np.array(res['c'])
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

def get_top_30_gainers():
    # Get all NSE stock symbols from Finnhub
    symbols_data = finnhub_client.stock_symbols('NSE')
    nse_symbols = [s['symbol'] + '.NS' for s in symbols_data if s.get('symbol')]

    gainers = []
    today_ts = unix_timestamp(date.today())
    
    for symbol in nse_symbols:
        # Fetch candles for just today and previous day to calculate gain %
        try:
            res = finnhub_client.stock_candles(symbol, 'D', today_ts - 7*86400, today_ts)  # last 7 days for safety
            
            if res['s'] != 'ok' or 'c' not in res or len(res['c']) < 2:
                continue
            
            close_prices = np.array(res['c'])
            # Calculate percentage gain from previous day to today
            gain_pct = (close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100
            gainers.append((symbol, gain_pct))
        except:
            continue

    # Sort by gain percentage descending and take top 30
    gainers = sorted(gainers, key=lambda x: x[1], reverse=True)[:30]
    return [g[0] for g in gainers]

# Get top 30 gainers list
top_30_symbols = get_top_30_gainers()

lines = [
    "# Top 30 Daily Gainers NSE Stocks with Metrics (Last 30 Days)\n\n",
    f"*Last updated on: {now}*\n\n",
    "| Stock Symbol | Profit/Loss (INR) | Win Rate (%) | Max Drawdown (INR) | Sharpe Ratio |\n",
    "| ------------ | ----------------- | ------------ | ------------------ | ------------ |\n"
]

for symbol in top_30_symbols:
    metrics = calculate_metrics(symbol)
    if metrics:
        profit_loss, win_rate, max_drawdown, sharpe_ratio = metrics
        lines.append(f"| {symbol} | {profit_loss:.2f} | {win_rate:.2f} | {max_drawdown:.2f} | {sharpe_ratio:.2f} |\n")
    else:
        lines.append(f"| {symbol} | N/A | N/A | N/A | N/A |\n")

if os.path.exists("README.md"):
    if not os.path.exists("history"):
        os.makedirs("history")
    shutil.copy(
        "README.md",
        f"history/README_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )

with open("README.md", "w", encoding="utf-8") as f:
    f.writelines(lines)

