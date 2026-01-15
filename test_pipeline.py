"""Quick test script to verify pipeline setup"""

import os
import sys
from pathlib import Path

def check_directory(path, name):
    """Check if directory exists"""
    if Path(path).exists():
        print(f"[OK] {name} directory exists: {path}")
        return True
    else:
        print(f"[FAIL] {name} directory missing: {path}")
        return False

def check_files(path, pattern, name):
    """Check if files exist"""
    files = list(Path(path).glob(pattern))
    if files:
        print(f"[OK] {name}: Found {len(files)} file(s)")
        return True
    else:
        print(f"[FAIL] {name}: No files found")
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
    if Path("src/ingest_data.py").exists():
        print("[OK] src/ingest_data.py")
        checks.append(True)
    else:
        print("[FAIL] src/ingest_data.py missing")
        checks.append(False)
    
    if Path("src/data_quality.py").exists():
        print("[OK] src/data_quality.py")
        checks.append(True)
    else:
        print("[FAIL] src/data_quality.py missing")
        checks.append(False)
    
    if Path("dbt_project.yml").exists():
        print("[OK] dbt_project.yml")
        checks.append(True)
    else:
        print("[FAIL] dbt_project.yml missing")
        checks.append(False)
    
    if Path("requirements.txt").exists():
        print("[OK] requirements.txt")
        checks.append(True)
    else:
        print("[FAIL] requirements.txt missing")
        checks.append(False)
    
    # Check for data files
    print("\nData Files:")
    bronze_files = list(Path("data/bronze").glob("*.parquet"))
    if bronze_files:
        print(f"[OK] Bronze layer data: Found {len(bronze_files)} file(s)")
        checks.append(True)
    else:
        print("[INFO] Bronze layer data: No files found (run ingestion first)")
        checks.append(False)
    
    silver_files = list(Path("data/silver").glob("*.parquet"))
    if silver_files:
        print(f"[OK] Silver layer data: Found {len(silver_files)} file(s)")
        checks.append(True)
    else:
        print("[INFO] Silver layer data: No files found (will be created by dbt)")
        # Don't fail on this, it's optional
    
    # Test imports
    print("\nPython Packages:")
    try:
        import duckdb
        print("[OK] duckdb")
        checks.append(True)
    except ImportError:
        print("[FAIL] duckdb - Install with: pip install duckdb")
        checks.append(False)
    
    try:
        import pandas
        print("[OK] pandas")
        checks.append(True)
    except ImportError:
        print("[FAIL] pandas - Install with: pip install pandas")
        checks.append(False)
    
    try:
        import yfinance
        print("[OK] yfinance")
        checks.append(True)
    except ImportError:
        print("[FAIL] yfinance - Install with: pip install yfinance")
        checks.append(False)
    
    try:
        import pyarrow
        print("[OK] pyarrow")
        checks.append(True)
    except ImportError:
        print("[FAIL] pyarrow - Install with: pip install pyarrow")
        checks.append(False)
    
    # Check Docker (optional)
    print("\nDocker (Optional):")
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Docker installed: {result.stdout.strip()}")
        else:
            print("[INFO] Docker not found (needed for PostgreSQL)")
    except FileNotFoundError:
        print("[INFO] Docker not found (needed for PostgreSQL)")
    
    # Summary
    print("\n" + "="*60)
    passed = sum(checks)
    total = len(checks)
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("[SUCCESS] All critical checks passed! Pipeline is ready.")
        print("\nNext steps:")
        print("1. python src/ingest_data.py")
        print("2. python src/data_quality.py")
        print("3. dbt run")
        return 0
    else:
        print("[WARNING] Some checks failed. Please install missing dependencies.")
        print("\nRun: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
