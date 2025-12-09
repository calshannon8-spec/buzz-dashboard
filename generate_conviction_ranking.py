#!/usr/bin/env python3
"""
Generate conviction ranking based on Max Weight Count from BuzzIndex_historical.csv
Max Weight Count = Number of times a ticker had the maximum weight in the index
"""

import pandas as pd
from pathlib import Path

# Read the historical data
csv_path = Path(__file__).parent / "BuzzIndex_historical.csv"
df = pd.read_csv(csv_path)

# Normalize ticker names for companies that changed names
# FB -> META (Facebook rebranded to Meta in 2021)
df['Ticker'] = df['Ticker'].replace({'FB': 'META'})

# Remove delisted/private companies
# TWTR was taken private
df = df[df['Ticker'] != 'TWTR']

# Convert Rebalance_date to datetime
df['Rebalance_date'] = pd.to_datetime(df['Rebalance_date'], format='%d/%m/%Y')

# Group by rebalance date and find max weight for each date
max_weight_counts = {}

for date in df['Rebalance_date'].unique():
    # Get all tickers for this date
    date_df = df[df['Rebalance_date'] == date]

    # Find the maximum weight for this date
    max_weight = date_df['Weight'].max()

    # Find all tickers that achieved this maximum weight
    max_weight_tickers = date_df[date_df['Weight'] == max_weight]['Ticker'].values

    # Increment count for each ticker that hit max weight
    for ticker in max_weight_tickers:
        if ticker not in max_weight_counts:
            max_weight_counts[ticker] = 0
        max_weight_counts[ticker] += 1

# Create results dataframe
results = []
for ticker, count in max_weight_counts.items():
    results.append({
        'Ticker': ticker,
        'Max Weight Count': count
    })

results_df = pd.DataFrame(results)

# Sort by Max Weight Count in descending order
results_df = results_df.sort_values('Max Weight Count', ascending=False)

# Save to CSV
output_path = Path(__file__).parent / "BUZZ_Highest_Sentiment_Metric.csv"
results_df.to_csv(output_path, index=False)

print(f"✓ Created {output_path.name}")
print(f"✓ Analyzed {len(df['Rebalance_date'].unique())} rebalance dates")
print(f"✓ Found {len(results_df)} unique tickers")
print(f"\nTop 10 Tickers by Max Weight Count:")
print(results_df.head(10).to_string(index=False))
