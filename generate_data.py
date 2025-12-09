import pandas as pd
import numpy as np
from pathlib import Path


def generate_month_starts(n_months: int = 36) -> pd.DatetimeIndex:
    """
    Generate a DatetimeIndex of month-start dates for the last n_months,
    including the current month.
    """
    today = pd.Timestamp.today().normalize()
    current_month_start = today.replace(day=1)
    month_starts = pd.date_range(
        end=current_month_start,
        periods=n_months,
        freq="MS"  # Month Start
    )
    return month_starts


def _find_latest_buzz_file() -> Path:
    """Find the most recent BUZZ_asof_*.csv in this folder or one level up."""
    base_dir = Path(__file__).resolve().parent
    candidates = list(base_dir.glob("BUZZ_asof_*.csv")) + list((base_dir.parent).glob("BUZZ_asof_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No BUZZ_asof_*.csv file found in {base_dir} or {base_dir.parent}")
    # Pick the newest by modification time
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return newest


def load_buzz_tickers(csv_path: str | None = None) -> list[str]:
    """
    Load tickers from the BUZZ holdings CSV and return a clean list.
    - If csv_path is provided, verify it exists (check current folder, then parent).
    - Otherwise, automatically pick the most recent BUZZ_asof_*.csv nearby.
    """
    base_dir = Path(__file__).resolve().parent
    path: Path

    if csv_path:
        candidate = base_dir / csv_path
        if not candidate.exists():
            alt = base_dir.parent / csv_path
            if alt.exists():
                candidate = alt
            else:
                raise FileNotFoundError(f"Holdings file not found: {candidate} or {alt}")
        path = candidate
    else:
        path = _find_latest_buzz_file()

    # The file has two preamble rows before the header row; skip them
    df = pd.read_csv(path, skiprows=2)
    if "Ticker" not in df.columns:
        raise ValueError("Ticker column not found in holdings CSV")

    # Keep only stock rows, strip country suffix (e.g., 'META US' -> 'META')
    df = df[df["Asset Class"].str.contains("Stock", na=False)].copy()
    df["TickerClean"] = df["Ticker"].astype(str).str.split().str[0]

    tickers = df["TickerClean"].dropna().tolist()
    if not tickers:
        raise ValueError("No tickers found after cleaning holdings CSV")
    return tickers


def generate_mock_data(n_months: int = 36, rows_per_month: int = 75) -> pd.DataFrame:
    """
    Generate mock BUZZ-style holdings history.

    Columns:
        - Date (YYYY-MM-DD, month-level)
        - Ticker
        - Sentiment_Score (0-100)
        - Rank (1-75)
        - Weight (0.5% - 3.0%)

    Ensures:
        - Exactly `rows_per_month` rows per month.
        - 'PLTR', 'NVDA', 'AMD' appear every single month.
    """
    np.random.seed(42)  # for reproducibility

    tickers_pool = load_buzz_tickers()
    # Make sure we have at least rows_per_month tickers; allow reuse with replacement if not
    if len(tickers_pool) < rows_per_month:
        # Repeat the list until we have enough to sample without replacement
        repeats = (rows_per_month // len(tickers_pool)) + 1
        tickers_pool = (tickers_pool * repeats)[: rows_per_month]

    # Ensure a few key names appear every month (take from the top of the list)
    base_tickers = tickers_pool[:3]

    month_starts = generate_month_starts(n_months)
    all_rows = []

    for month_start in month_starts:
        # Ensure our key names are always present
        month_tickers = base_tickers.copy()

        # Fill out the rest of the names for the month
        remaining_needed = rows_per_month - len(month_tickers)
        available = [t for t in tickers_pool if t not in month_tickers]
        # If we don't have enough unique names left, allow reuse
        replace = len(available) < remaining_needed
        sampled_extra = np.random.choice(available, size=remaining_needed, replace=replace)
        month_tickers.extend(sampled_extra.tolist())

        # Generate a random rank ordering 1-75
        ranks = np.arange(1, rows_per_month + 1)
        np.random.shuffle(ranks)

        # Generate random sentiment scores and weights for each ticker
        sentiment_scores = np.random.uniform(0, 100, size=rows_per_month)
        weights = np.random.uniform(0.5, 3.0, size=rows_per_month)

        for ticker, rank, sentiment, weight in zip(
            month_tickers, ranks, sentiment_scores, weights
        ):
            all_rows.append(
                {
                    "Date": month_start.strftime("%Y-%m-%d"),
                    "Ticker": ticker,
                    "Sentiment_Score": round(float(sentiment), 2),
                    "Rank": int(rank),
                    "Weight": round(float(weight), 3),
                }
            )

    df = pd.DataFrame(all_rows)
    return df


def main():
    df = generate_mock_data(n_months=36, rows_per_month=75)
    output_path = Path(__file__).resolve().parent / "buzz_mock_history.csv"
    df.to_csv(output_path, index=False)
    print(f"Mock data written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
