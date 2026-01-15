"""
Setup script for Data Lakehouse project
Installs dependencies and sets up the project structure
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during {description}:")
        print(e.stderr)
        return False

def main():
    print("="*60)
    print("Data Lakehouse Setup")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("✗ Python 3.9+ is required")
        sys.exit(1)
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install Python dependencies
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python dependencies"):
        print("Warning: Some dependencies may have failed to install")
    
    # Verify critical packages
    print("\nVerifying critical packages...")
    critical_packages = ['duckdb', 'pandas', 'yfinance', 'pyarrow']
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing - please install manually")
    
    # Check for dbt
    try:
        result = subprocess.run(['dbt', '--version'], capture_output=True, text=True)
        print("✓ dbt is installed")
    except FileNotFoundError:
        print("⚠ dbt is not installed. Install with: pip install dbt-duckdb")
    
    # Check for Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        print("✓ Docker is installed")
    except FileNotFoundError:
        print("⚠ Docker is not installed. Install Docker Desktop for your OS")
    
    # Ensure directories exist
    print("\nChecking project structure...")
    directories = ['data/bronze', 'data/silver', 'data/gold', 'src', 'models/staging', 'models/silver', 'models/gold']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory}/")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start PostgreSQL: docker-compose up -d")
    print("2. Configure dbt: Copy profiles.yml.example to ~/.dbt/profiles.yml")
    print("3. Run pipeline: python src/orchestrate_pipeline.py")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
