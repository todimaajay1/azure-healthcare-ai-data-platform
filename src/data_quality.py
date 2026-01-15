"""
Data Quality Checks for Bronze to Silver Layer Transition
Performs validation checks to ensure data integrity before promotion to Silver layer.
"""

import os
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BRONZE_PATH = Path("data/bronze")
SILVER_PATH = Path("data/silver")
CRITICAL_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume', 'symbol', 'date']  # Columns that must not be null


class DataQualityChecker:
    """Handles data quality validation before Silver layer promotion"""
    
    def __init__(self, critical_columns: List[str] = None):
        """
        Initialize Data Quality Checker
        
        Args:
            critical_columns: List of column names that must not contain null values
        """
        self.critical_columns = critical_columns or CRITICAL_COLUMNS
        self.quality_results = []
        
    def check_null_values(self, df: pd.DataFrame, file_name: str) -> Tuple[bool, Dict]:
        """
        Check for null values in critical columns
        
        Args:
            df: DataFrame to check
            file_name: Name of the source file for reporting
        
        Returns:
            Tuple of (is_valid, results_dict)
        """
        results = {
            'file_name': file_name,
            'total_rows': len(df),
            'null_counts': {},
            'has_nulls': False,
            'failed_columns': []
        }
        
        for column in self.critical_columns:
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found in {file_name}. Available columns: {list(df.columns)}")
                results['failed_columns'].append(column)
                results['has_nulls'] = True
                continue
            
            null_count = df[column].isnull().sum()
            results['null_counts'][column] = null_count
            
            if null_count > 0:
                logger.error(f"Found {null_count} null values in column '{column}' for {file_name}")
                results['has_nulls'] = True
                results['failed_columns'].append(column)
        
        is_valid = not results['has_nulls']
        
        if is_valid:
            logger.info(f"✓ Null check passed for {file_name}")
        else:
            logger.error(f"✗ Null check failed for {file_name}")
        
        return is_valid, results
    
    def check_data_types(self, df: pd.DataFrame, file_name: str) -> Tuple[bool, Dict]:
        """
        Check for expected data types in critical columns
        
        Args:
            df: DataFrame to check
            file_name: Name of the source file for reporting
        
        Returns:
            Tuple of (is_valid, results_dict)
        """
        results = {
            'file_name': file_name,
            'type_mismatches': {},
            'has_mismatches': False
        }
        
        expected_types = {
            'Open': ['float64', 'float32'],
            'High': ['float64', 'float32'],
            'Low': ['float64', 'float32'],
            'Close': ['float64', 'float32'],
            'Volume': ['int64', 'int32', 'float64', 'float32']
        }
        
        for column, expected in expected_types.items():
            if column in df.columns:
                actual_type = str(df[column].dtype)
                if actual_type not in expected:
                    results['type_mismatches'][column] = {
                        'expected': expected,
                        'actual': actual_type
                    }
                    results['has_mismatches'] = True
                    logger.warning(f"Type mismatch in '{column}' for {file_name}: expected {expected}, got {actual_type}")
        
        is_valid = not results['has_mismatches']
        return is_valid, results
    
    def check_data_range(self, df: pd.DataFrame, file_name: str) -> Tuple[bool, Dict]:
        """
        Check for logical data ranges (e.g., High >= Low, prices > 0)
        
        Args:
            df: DataFrame to check
            file_name: Name of the source file for reporting
        
        Returns:
            Tuple of (is_valid, results_dict)
        """
        results = {
            'file_name': file_name,
            'violations': [],
            'has_violations': False
        }
        
        if 'High' in df.columns and 'Low' in df.columns:
            invalid_rows = df[df['High'] < df['Low']]
            if len(invalid_rows) > 0:
                results['violations'].append(f"{len(invalid_rows)} rows where High < Low")
                results['has_violations'] = True
                logger.error(f"Found {len(invalid_rows)} rows where High < Low in {file_name}")
        
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                negative_prices = df[df[col] < 0]
                if len(negative_prices) > 0:
                    results['violations'].append(f"{len(negative_prices)} rows with negative {col}")
                    results['has_violations'] = True
                    logger.error(f"Found {len(negative_prices)} rows with negative {col} in {file_name}")
        
        is_valid = not results['has_violations']
        return is_valid, results
    
    def validate_file(self, file_path: Path) -> Tuple[bool, Dict]:
        """
        Perform all quality checks on a bronze layer file
        
        Args:
            file_path: Path to the Parquet file to validate
        
        Returns:
            Tuple of (is_valid, combined_results_dict)
        """
        logger.info(f"Validating file: {file_path.name}")
        
        try:
            df = pd.read_parquet(file_path)
            
            # Run all checks
            null_valid, null_results = self.check_null_values(df, file_path.name)
            type_valid, type_results = self.check_data_types(df, file_path.name)
            range_valid, range_results = self.check_data_range(df, file_path.name)
            
            combined_results = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'total_rows': len(df),
                'null_check': null_results,
                'type_check': type_results,
                'range_check': range_results,
                'all_checks_passed': null_valid and type_valid and range_valid
            }
            
            self.quality_results.append(combined_results)
            
            return combined_results['all_checks_passed'], combined_results
            
        except Exception as e:
            logger.error(f"Error validating {file_path.name}: {str(e)}")
            return False, {'error': str(e), 'file_name': file_path.name}
    
    def validate_bronze_layer(self) -> Dict:
        """
        Validate all files in the bronze layer
        
        Returns:
            Dictionary with validation summary
        """
        logger.info("Starting bronze layer validation")
        
        bronze_files = list(BRONZE_PATH.glob("*.parquet"))
        
        if not bronze_files:
            logger.warning("No Parquet files found in bronze layer")
            return {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'results': []
            }
        
        logger.info(f"Found {len(bronze_files)} files to validate")
        
        valid_count = 0
        invalid_count = 0
        
        for file_path in bronze_files:
            is_valid, results = self.validate_file(file_path)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        summary = {
            'total_files': len(bronze_files),
            'valid_files': valid_count,
            'invalid_files': invalid_count,
            'results': self.quality_results
        }
        
        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid files")
        
        return summary


def promote_to_silver(file_path: Path, validated: bool = True):
    """
    Move validated file from bronze to silver layer
    
    Args:
        file_path: Path to the validated bronze file
        validated: Whether the file passed quality checks
    """
    if not validated:
        logger.warning(f"Skipping promotion of {file_path.name} - failed quality checks")
        return
    
    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    
    try:
        destination = SILVER_PATH / file_path.name
        import shutil
        shutil.copy2(file_path, destination)
        logger.info(f"Promoted {file_path.name} to silver layer")
    except Exception as e:
        logger.error(f"Error promoting {file_path.name} to silver: {str(e)}")


if __name__ == "__main__":
    # Example usage
    logger.info("Starting data quality checks")
    
    checker = DataQualityChecker()
    summary = checker.validate_bronze_layer()
    
    # Print summary
    print("\n" + "="*50)
    print("DATA QUALITY SUMMARY")
    print("="*50)
    print(f"Total files: {summary['total_files']}")
    print(f"Valid files: {summary['valid_files']}")
    print(f"Invalid files: {summary['invalid_files']}")
    print("="*50 + "\n")
