"""
Data Ingestion Script for Bronze Layer
Pulls real-time financial market data from Yahoo Finance API
and saves as Parquet files in the data/bronze folder.
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BRONZE_PATH = Path("data/bronze")
SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ"]  # Sample symbols
TICKER_INTERVAL = "1d"  # Daily data
PERIOD = "1mo"  # 1 month of historical data


def ensure_bronze_directory():
    """Ensure the bronze directory exists"""
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    logger.info(f"Bronze directory ready at {BRONZE_PATH.absolute()}")


def fetch_stock_data(symbol: str, period: str = PERIOD, interval: str = TICKER_INTERVAL) -> pd.DataFrame:
    """
    Fetch stock data from Yahoo Finance API
    
    Args:
        symbol: Stock ticker symbol
        period: Period of historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    
    Returns:
        DataFrame with stock data
    """
    try:
        logger.info(f"Fetching data for symbol: {symbol}")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data retrieved for {symbol}")
            return pd.DataFrame()
        
        # Add metadata columns
        df.reset_index(inplace=True)
        df['symbol'] = symbol
        df['ingestion_timestamp'] = datetime.now()
        df['data_source'] = 'yahoo_finance'
        
        # Rename Date column if it exists
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
        
        logger.info(f"Successfully fetched {len(df)} records for {symbol}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()


def save_to_bronze(df: pd.DataFrame, symbol: str):
    """
    Save DataFrame to bronze layer as Parquet file
    
    Args:
        df: DataFrame to save
        symbol: Stock symbol for filename
    """
    if df.empty:
        logger.warning(f"Skipping save for {symbol} - empty DataFrame")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stock_data_{symbol}_{timestamp}.parquet"
    filepath = BRONZE_PATH / filename
    
    try:
        df.to_parquet(filepath, engine='pyarrow', index=False)
        logger.info(f"Saved {len(df)} records to {filepath}")
    except Exception as e:
        logger.error(f"Error saving data for {symbol}: {str(e)}")


def ingest_all_symbols(symbols: list = None):
    """
    Ingest data for all configured symbols
    
    Args:
        symbols: List of stock symbols to ingest. If None, uses default SYMBOLS
    """
    if symbols is None:
        symbols = SYMBOLS
    
    ensure_bronze_directory()
    
    logger.info(f"Starting ingestion for {len(symbols)} symbols")
    
    for symbol in symbols:
        df = fetch_stock_data(symbol)
        if not df.empty:
            save_to_bronze(df, symbol)
    
    logger.info("Ingestion completed")


if __name__ == "__main__":
    # Example usage
    logger.info("Starting data ingestion process")
    ingest_all_symbols()
    logger.info("Data ingestion process completed")
