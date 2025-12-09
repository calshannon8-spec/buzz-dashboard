#!/usr/bin/env python3
"""
Generate Monthly Portfolio Turnover Rate time series from BuzzIndex_historical.csv

Portfolio Turnover Rate = (Sum of Absolute Weight Changes) / 2
This measures the percentage of the portfolio that changes each month.
"""

import pandas as pd
from pathlib import Path

# Read the historical data
csv_path = Path(__file__).parent / "BuzzIndex_historical.csv"
df = pd.read_csv(csv_path)

# Normalize ticker names for companies that changed names
df['Ticker'] = df['Ticker'].replace({'FB': 'META'})

# Remove delisted/private companies
df = df[df['Ticker'] != 'TWTR']

# Convert Rebalance_date to datetime
df['Rebalance_date'] = pd.to_datetime(df['Rebalance_date'], format='%d/%m/%Y')

# Sort by date
df = df.sort_values('Rebalance_date')

# Get unique rebalance dates
dates = sorted(df['Rebalance_date'].unique())

# Calculate turnover rate for each consecutive pair of dates
turnover_data = []

for i in range(1, len(dates)):
    prev_date = dates[i-1]
    curr_date = dates[i]

    # Get portfolios for both dates
    prev_portfolio = df[df['Rebalance_date'] == prev_date][['Ticker', 'Weight']].set_index('Ticker')
    curr_portfolio = df[df['Rebalance_date'] == curr_date][['Ticker', 'Weight']].set_index('Ticker')

    # Combine both portfolios to see all tickers
    all_tickers = set(prev_portfolio.index) | set(curr_portfolio.index)

    # Calculate absolute weight changes
    total_absolute_change = 0

    for ticker in all_tickers:
        prev_weight = prev_portfolio.loc[ticker, 'Weight'] if ticker in prev_portfolio.index else 0
        curr_weight = curr_portfolio.loc[ticker, 'Weight'] if ticker in curr_portfolio.index else 0

        absolute_change = abs(curr_weight - prev_weight)
        total_absolute_change += absolute_change

    # Turnover rate is half of the total absolute change
    # (because each trade involves both a buy and a sell)
    turnover_rate = total_absolute_change / 2

    # Convert to percentage
    turnover_rate_pct = turnover_rate * 100

    turnover_data.append({
        'Rebalance_date': curr_date,
        'Monthly_Turnover_Rate_Percent': round(turnover_rate_pct, 2)
    })

# Create DataFrame
turnover_df = pd.DataFrame(turnover_data)

# Calculate average turnover rate
avg_turnover = turnover_df['Monthly_Turnover_Rate_Percent'].mean()

# Save to CSV
output_path = Path(__file__).parent / "BUZZ_Monthly_Turnover_Time_Series.csv"
turnover_df.to_csv(output_path, index=False)

print(f"✓ Created {output_path.name}")
print(f"✓ Analyzed {len(turnover_df)} monthly transitions")
print(f"✓ Average Monthly Turnover Rate: {avg_turnover:.2f}%")
print(f"✓ Min Turnover: {turnover_df['Monthly_Turnover_Rate_Percent'].min():.2f}%")
print(f"✓ Max Turnover: {turnover_df['Monthly_Turnover_Rate_Percent'].max():.2f}%")
print(f"\nFirst 5 months:")
print(turnover_df.head().to_string(index=False))
