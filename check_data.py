"""Script to check and query data in the lakehouse"""

import sys
from pathlib import Path

try:
    import duckdb
    import pandas as pd
except ImportError as e:
    print(f"Error: Missing required package. Install with: pip install duckdb pandas")
    print(f"Details: {e}")
    sys.exit(1)

def check_bronze_layer():
    """Check bronze layer files"""
    print("\n" + "="*60)
    print("BRONZE LAYER CHECK")
    print("="*60)
    
    bronze_files = list(Path("data/bronze").glob("*.parquet"))
    
    if not bronze_files:
        print("[FAIL] No Parquet files found in data/bronze/")
        print("  Run: python src/ingest_data.py")
        return False
    
    print(f"[OK] Found {len(bronze_files)} file(s) in bronze layer")
    
    # Try to read one file
    try:
        df = pd.read_parquet(bronze_files[0])
        print(f"\nSample file: {bronze_files[0].name}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head(3).to_string())
        return True
    except Exception as e:
        print(f"[ERROR] Error reading Parquet file: {e}")
        return False

def check_silver_layer():
    """Check silver layer files"""
    print("\n" + "="*60)
    print("SILVER LAYER CHECK")
    print("="*60)
    
    silver_files = list(Path("data/silver").glob("*.parquet"))
    
    if not silver_files:
        print("[INFO] No Parquet files found in data/silver/")
        print("  This is normal - silver data is created by dbt or quality checks")
        return None
    
    print(f"[OK] Found {len(silver_files)} file(s) in silver layer")
    
    try:
        df = pd.read_parquet(silver_files[0])
        print(f"\nSample file: {silver_files[0].name}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        return True
    except Exception as e:
        print(f"[ERROR] Error reading Parquet file: {e}")
        return False

def check_duckdb_models():
    """Check DuckDB models if database exists"""
    print("\n" + "="*60)
    print("DUCKDB MODELS CHECK")
    print("="*60)
    
    db_path = "data_lakehouse.duckdb"
    
    if not Path(db_path).exists():
        print("[INFO] DuckDB database not found")
        print("  Database will be created when you run: dbt run")
        return None
    
    try:
        conn = duckdb.connect(db_path)
        
        # Check staging schema
        try:
            result = conn.execute("SELECT COUNT(*) as count FROM staging.stg_stock_data").fetchone()
            print(f"[OK] staging.stg_stock_data: {result[0]} rows")
            
            # Show sample
            sample = conn.execute("SELECT * FROM staging.stg_stock_data LIMIT 3").fetchdf()
            print("\nSample from staging:")
            print(sample.to_string())
        except Exception as e:
            print(f"[INFO] staging.stg_stock_data: {e}")
        
        # Check silver schema
        try:
            result = conn.execute("SELECT COUNT(*) as count FROM silver.silver_stock_data").fetchone()
            print(f"\n[OK] silver.silver_stock_data: {result[0]} rows")
        except Exception as e:
            print(f"[INFO] silver.silver_stock_data: {e}")
        
        # Check gold schema
        try:
            result = conn.execute("SELECT COUNT(*) as count FROM gold.gold_daily_metrics").fetchone()
            print(f"[OK] gold.gold_daily_metrics: {result[0]} rows")
        except Exception as e:
            print(f"[INFO] gold.gold_daily_metrics: {e}")
        
        try:
            result = conn.execute("SELECT COUNT(*) as count FROM gold.gold_symbol_summary").fetchone()
            print(f"[OK] gold.gold_symbol_summary: {result[0]} rows")
            
            # Show summary
            summary = conn.execute("SELECT * FROM gold.gold_symbol_summary").fetchdf()
            print("\nSymbol Summary:")
            print(summary.to_string())
        except Exception as e:
            print(f"[INFO] gold.gold_symbol_summary: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Error connecting to DuckDB: {e}")
        return False

def main():
    print("="*60)
    print("DATA LAKEHOUSE DATA CHECK")
    print("="*60)
    
    # Check layers
    bronze_ok = check_bronze_layer()
    silver_ok = check_silver_layer()
    duckdb_ok = check_duckdb_models()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if bronze_ok:
        print("[OK] Bronze layer: Data found")
    else:
        print("[FAIL] Bronze layer: No data - run ingestion first")
    
    if silver_ok is True:
        print("[OK] Silver layer: Data found")
    elif silver_ok is None:
        print("[INFO] Silver layer: Not created yet (normal)")
    
    if duckdb_ok is True:
        print("[OK] DuckDB models: Accessible")
    elif duckdb_ok is None:
        print("[INFO] DuckDB models: Not created yet - run 'dbt run'")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
