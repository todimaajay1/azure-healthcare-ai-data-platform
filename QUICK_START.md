# Quick Start Guide - Running and Checking Your Data Lakehouse

## Step-by-Step Instructions

### 1. Initial Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# OR use the automated setup script
python setup.py
```

### 2. Start PostgreSQL Metadata Database

```bash
# Start PostgreSQL in Docker
docker-compose up -d

# Check if it's running
docker-compose ps

# View logs if needed
docker-compose logs postgres-metadata
```

### 3. Configure dbt (First Time Only)

```bash
# Create dbt profiles directory (Windows)
mkdir -p $env:USERPROFILE\.dbt

# Copy the example profile
copy profiles.yml.example $env:USERPROFILE\.dbt\profiles.yml

# Edit the profiles.yml file if needed
# The default path should work, but you can customize it
```

### 4. Run Data Ingestion (Bronze Layer)

```bash
# Ingest financial data from Yahoo Finance
python src/ingest_data.py
```

**What to Check:**
- Files should appear in `data/bronze/` folder
- Files should be named like `stock_data_AAPL_YYYYMMDD_HHMMSS.parquet`
- Check console output for success messages

### 5. Run Data Quality Checks

```bash
# Validate data quality before Silver layer
python src/data_quality.py
```

**What to Check:**
- Console should show validation summary
- Should indicate number of valid/invalid files
- No critical errors should appear

### 6. Run dbt Transformations

```bash
# First, test dbt connection
dbt debug

# Run all transformations (Staging → Silver → Gold)
dbt run

# OR run specific layers
dbt run --select staging
dbt run --select silver
dbt run --select gold
```

**What to Check:**
- dbt should compile and run successfully
- No error messages
- Check `target/` folder for compiled SQL

### 7. Run dbt Tests

```bash
# Run all data quality tests
dbt test

# Run specific tests
dbt test --select test_silver_data_quality
```

**What to Check:**
- All tests should pass
- If tests fail, check the error messages

### 8. Run Complete Pipeline (All-in-One)

```bash
# Run everything: Ingestion → Quality → dbt → Tests
python src/orchestrate_pipeline.py

# Skip ingestion if data already exists
python src/orchestrate_pipeline.py --skip-ingestion

# Skip tests for faster execution
python src/orchestrate_pipeline.py --skip-tests
```

**What to Check:**
- Pipeline summary at the end
- All steps should show "✓ Completed"
- Check `pipeline.log` for detailed logs

---

## Verification Checklist

### ✅ Verify Bronze Layer
```bash
# Check if Parquet files exist
ls data/bronze/*.parquet

# Or in PowerShell
Get-ChildItem data\bronze\*.parquet
```

### ✅ Verify Silver Layer
```bash
# Check if validated files exist
ls data/silver/*.parquet
```

### ✅ Verify dbt Models
```bash
# Check compiled models
ls target/compiled/

# View dbt documentation
dbt docs generate
dbt docs serve
```

### ✅ Query DuckDB Database

```python
# Python script to query the data
import duckdb

# Connect to the database
conn = duckdb.connect('data_lakehouse.duckdb')

# Query staging layer
result = conn.execute("SELECT * FROM staging.stg_stock_data LIMIT 10").fetchall()
print("Staging Data:")
print(result)

# Query silver layer
result = conn.execute("SELECT * FROM silver.silver_stock_data LIMIT 10").fetchall()
print("\nSilver Data:")
print(result)

# Query gold layer
result = conn.execute("SELECT * FROM gold.gold_daily_metrics LIMIT 10").fetchall()
print("\nGold Metrics:")
print(result)

# Summary statistics
result = conn.execute("SELECT * FROM gold.gold_symbol_summary").fetchall()
print("\nSymbol Summary:")
print(result)

conn.close()
```

---

## Troubleshooting

### Issue: Python packages not found
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Docker not running
**Solution:**
- Start Docker Desktop
- Check with: `docker ps`

### Issue: dbt command not found
**Solution:**
```bash
pip install dbt-duckdb
```

### Issue: dbt debug fails
**Solution:**
- Check profiles.yml exists in `~/.dbt/` or `$env:USERPROFILE\.dbt\`
- Verify database path in profiles.yml
- Try: `dbt debug --config-dir`

### Issue: No data in bronze folder
**Solution:**
- Check internet connection
- Verify yfinance is installed: `pip install yfinance`
- Check API rate limits (may need to wait between requests)

### Issue: DuckDB connection errors
**Solution:**
- Database file will be created automatically
- Check file permissions
- Ensure DuckDB is installed: `pip install duckdb`

---

## Quick Test Script

Save this as `test_pipeline.py`:

```python
"""Quick test script to verify pipeline setup"""

import os
import sys
from pathlib import Path

def check_directory(path, name):
    """Check if directory exists"""
    if Path(path).exists():
        print(f"✓ {name} directory exists: {path}")
        return True
    else:
        print(f"✗ {name} directory missing: {path}")
        return False

def check_files(path, pattern, name):
    """Check if files exist"""
    files = list(Path(path).glob(pattern))
    if files:
        print(f"✓ {name}: Found {len(files)} file(s)")
        return True
    else:
        print(f"✗ {name}: No files found")
        return False

def main():
    print("="*60)
    print("Data Lakehouse Setup Verification")
    print("="*60)
    
    # Check directories
    checks = []
    checks.append(check_directory("data/bronze", "Bronze"))
    checks.append(check_directory("data/silver", "Silver"))
    checks.append(check_directory("data/gold", "Gold"))
    checks.append(check_directory("src", "Source"))
    checks.append(check_directory("models", "Models"))
    
    # Check key files
    checks.append(Path("src/ingest_data.py").exists())
    checks.append(Path("src/data_quality.py").exists())
    checks.append(Path("dbt_project.yml").exists())
    checks.append(Path("requirements.txt").exists())
    
    # Check for data files
    print("\nData Files:")
    checks.append(check_files("data/bronze", "*.parquet", "Bronze layer data"))
    checks.append(check_files("data/silver", "*.parquet", "Silver layer data"))
    
    # Test imports
    print("\nPython Packages:")
    try:
        import duckdb
        print("✓ duckdb")
    except ImportError:
        print("✗ duckdb")
        checks.append(False)
    
    try:
        import pandas
        print("✓ pandas")
    except ImportError:
        print("✗ pandas")
        checks.append(False)
    
    try:
        import yfinance
        print("✓ yfinance")
    except ImportError:
        print("✗ yfinance")
        checks.append(False)
    
    # Summary
    print("\n" + "="*60)
    if all(checks):
        print("✓ All checks passed! Pipeline is ready.")
        return 0
    else:
        print("✗ Some checks failed. Please review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Run it with: `python test_pipeline.py`
