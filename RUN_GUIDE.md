# How to Run and Check Your Data Lakehouse

## Quick Start - 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Complete Pipeline
```bash
python src/orchestrate_pipeline.py
```

### Step 3: Check Your Data
```bash
python check_data.py
```

---

## Detailed Step-by-Step Guide

### 1. Verify Setup
First, check if everything is ready:
```bash
python test_pipeline.py
```

This will show you:
- [OK] = Everything is good
- [FAIL] = Something needs to be fixed
- [INFO] = Informational (not an error)

### 2. Install Missing Packages (if needed)
If the test shows missing packages:
```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL (Optional but Recommended)
```bash
docker-compose up -d
```

Check if it's running:
```bash
docker-compose ps
```

### 4. Run Data Ingestion
Pull financial data from Yahoo Finance:
```bash
python src/ingest_data.py
```

**What happens:**
- Fetches stock data for 10 symbols (AAPL, GOOGL, MSFT, etc.)
- Saves as Parquet files in `data/bronze/`
- Each file is named like: `stock_data_AAPL_20240101_120000.parquet`

**Check results:**
```bash
# Windows PowerShell
Get-ChildItem data\bronze\*.parquet

# Or check with Python
python check_data.py
```

### 5. Run Quality Checks
Validate the data before moving to Silver:
```bash
python src/data_quality.py
```

**What it checks:**
- No null values in critical columns
- Data types are correct
- Logical constraints (High >= Low, prices > 0)

**Expected output:**
```
Validation complete: X valid, 0 invalid files
```

### 6. Run dbt Transformations

**First time setup:**
```bash
# Create dbt profiles directory (Windows)
mkdir $env:USERPROFILE\.dbt

# Copy the example profile
copy profiles.yml.example $env:USERPROFILE\.dbt\profiles.yml
```

**Run transformations:**
```bash
# Test dbt connection
dbt debug

# Run all models (staging → silver → gold)
dbt run

# Or run specific layers
dbt run --select staging
dbt run --select silver
dbt run --select gold
```

**What happens:**
- **Staging**: Cleans and standardizes data from bronze
- **Silver**: Validates and deduplicates data
- **Gold**: Creates aggregated metrics and summaries

### 7. Run dbt Tests
Check data quality:
```bash
dbt test
```

**Expected output:**
```
Completed successfully
```

### 8. Check Your Data
View what was created:
```bash
python check_data.py
```

This shows:
- Files in bronze/silver layers
- Row counts in DuckDB models
- Sample data from each layer

---

## All-in-One: Complete Pipeline

Run everything at once:
```bash
python src/orchestrate_pipeline.py
```

This runs:
1. Data ingestion → Bronze
2. Quality checks
3. dbt staging transformations
4. dbt silver transformations
5. dbt gold transformations
6. dbt tests

**Options:**
```bash
# Skip ingestion if data already exists
python src/orchestrate_pipeline.py --skip-ingestion

# Skip tests for faster execution
python src/orchestrate_pipeline.py --skip-tests
```

---

## Verify Everything Works

### Check 1: Files Exist
```bash
# Bronze files
Get-ChildItem data\bronze\*.parquet

# Silver files (after quality checks)
Get-ChildItem data\silver\*.parquet
```

### Check 2: DuckDB Database
```bash
# Check if database was created
Test-Path data_lakehouse.duckdb
```

### Check 3: Query the Data
```python
import duckdb

conn = duckdb.connect('data_lakehouse.duckdb')

# Check staging
result = conn.execute("SELECT COUNT(*) FROM staging.stg_stock_data").fetchone()
print(f"Staging rows: {result[0]}")

# Check silver
result = conn.execute("SELECT COUNT(*) FROM silver.silver_stock_data").fetchone()
print(f"Silver rows: {result[0]}")

# Check gold
result = conn.execute("SELECT COUNT(*) FROM gold.gold_daily_metrics").fetchone()
print(f"Gold rows: {result[0]}")

# View summary
summary = conn.execute("SELECT * FROM gold.gold_symbol_summary").fetchdf()
print(summary)

conn.close()
```

---

## Troubleshooting

### Problem: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "dbt: command not found"
**Solution:**
```bash
pip install dbt-duckdb
```

### Problem: "No data in bronze folder"
**Solution:**
- Check internet connection
- Yahoo Finance API might be rate-limiting
- Wait a few minutes and try again

### Problem: "DuckDB connection error"
**Solution:**
- Database is created automatically when you run `dbt run`
- Make sure you've run `dbt run` at least once

### Problem: "Docker not found"
**Solution:**
- PostgreSQL is optional for this setup
- You can skip it if you're just testing
- Install Docker Desktop if you need it

---

## Expected Results

After running the complete pipeline, you should have:

1. **Bronze Layer**: 10+ Parquet files (one per symbol)
2. **Silver Layer**: Validated Parquet files (if quality checks pass)
3. **DuckDB Database**: `data_lakehouse.duckdb` with:
   - `staging.stg_stock_data` - Cleaned raw data
   - `silver.silver_stock_data` - Validated data
   - `gold.gold_daily_metrics` - Daily aggregated metrics
   - `gold.gold_symbol_summary` - Symbol-level summaries

---

## Quick Reference Commands

```bash
# Setup
python setup.py
pip install -r requirements.txt

# Test
python test_pipeline.py

# Run pipeline
python src/orchestrate_pipeline.py

# Check data
python check_data.py

# Individual steps
python src/ingest_data.py
python src/data_quality.py
dbt run
dbt test
```

---

## Next Steps

Once everything is working:
1. Customize symbols in `src/ingest_data.py`
2. Add more dbt models in `models/`
3. Create custom data quality tests in `tests/`
4. Set up scheduling with Dagster or Airflow
