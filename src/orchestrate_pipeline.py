"""
Data Lakehouse Pipeline Orchestration Script
Runs the complete data pipeline: Ingestion → Quality Checks → dbt Transformations
"""

import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the data lakehouse pipeline execution"""
    
    def __init__(self):
        self.pipeline_start_time = datetime.now()
        self.steps_completed = []
        self.steps_failed = []
        
    def run_command(self, command: list, description: str) -> bool:
        """
        Run a shell command and log results
        
        Args:
            command: List of command and arguments
            description: Description of what the command does
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting: {description}")
        logger.info(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            
            logger.info(f"✓ Completed: {description}")
            self.steps_completed.append(description)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed: {description}")
            logger.error(f"Error: {e.stderr}")
            self.steps_failed.append(description)
            return False
        except FileNotFoundError as e:
            logger.error(f"✗ Command not found: {command[0]}")
            logger.error(f"Please ensure {command[0]} is installed and in PATH")
            self.steps_failed.append(description)
            return False
    
    def run_ingestion(self) -> bool:
        """Run data ingestion to bronze layer"""
        return self.run_command(
            [sys.executable, "src/ingest_data.py"],
            "Data Ingestion (Bronze Layer)"
        )
    
    def run_quality_checks(self) -> bool:
        """Run data quality checks"""
        return self.run_command(
            [sys.executable, "src/data_quality.py"],
            "Data Quality Checks"
        )
    
    def run_dbt_staging(self) -> bool:
        """Run dbt staging models"""
        return self.run_command(
            ["dbt", "run", "--select", "staging"],
            "dbt Staging Transformations"
        )
    
    def run_dbt_silver(self) -> bool:
        """Run dbt silver models"""
        return self.run_command(
            ["dbt", "run", "--select", "silver"],
            "dbt Silver Transformations"
        )
    
    def run_dbt_gold(self) -> bool:
        """Run dbt gold models"""
        return self.run_command(
            ["dbt", "run", "--select", "gold"],
            "dbt Gold Transformations"
        )
    
    def run_dbt_tests(self) -> bool:
        """Run dbt data quality tests"""
        return self.run_command(
            ["dbt", "test"],
            "dbt Data Quality Tests"
        )
    
    def run_full_pipeline(self, skip_ingestion: bool = False, run_tests: bool = True):
        """
        Run the complete data lakehouse pipeline
        
        Args:
            skip_ingestion: Skip data ingestion step (useful if data already exists)
            run_tests: Whether to run dbt tests after transformations
        """
        logger.info("="*60)
        logger.info("Starting Data Lakehouse Pipeline")
        logger.info("="*60)
        
        pipeline_steps = []
        
        # Step 1: Data Ingestion
        if not skip_ingestion:
            if not self.run_ingestion():
                logger.error("Pipeline failed at ingestion step. Stopping.")
                return self.print_summary()
            pipeline_steps.append("✓ Ingestion")
        else:
            logger.info("Skipping ingestion step")
            pipeline_steps.append("⊘ Ingestion (skipped)")
        
        # Step 2: Quality Checks
        if not self.run_quality_checks():
            logger.warning("Quality checks failed, but continuing pipeline...")
            pipeline_steps.append("⚠ Quality Checks (failed)")
        else:
            pipeline_steps.append("✓ Quality Checks")
        
        # Step 3: dbt Staging
        if not self.run_dbt_staging():
            logger.error("Pipeline failed at dbt staging step. Stopping.")
            return self.print_summary()
        pipeline_steps.append("✓ dbt Staging")
        
        # Step 4: dbt Silver
        if not self.run_dbt_silver():
            logger.error("Pipeline failed at dbt silver step. Stopping.")
            return self.print_summary()
        pipeline_steps.append("✓ dbt Silver")
        
        # Step 5: dbt Gold
        if not self.run_dbt_gold():
            logger.error("Pipeline failed at dbt gold step. Stopping.")
            return self.print_summary()
        pipeline_steps.append("✓ dbt Gold")
        
        # Step 6: dbt Tests (optional)
        if run_tests:
            if not self.run_dbt_tests():
                logger.warning("Some dbt tests failed, but pipeline completed.")
                pipeline_steps.append("⚠ dbt Tests (warnings)")
            else:
                pipeline_steps.append("✓ dbt Tests")
        else:
            pipeline_steps.append("⊘ dbt Tests (skipped)")
        
        logger.info("="*60)
        logger.info("Pipeline Execution Complete")
        logger.info("="*60)
        
        return self.print_summary()
    
    def print_summary(self):
        """Print pipeline execution summary"""
        duration = datetime.now() - self.pipeline_start_time
        
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        print(f"Duration: {duration}")
        print(f"Completed Steps: {len(self.steps_completed)}")
        print(f"Failed Steps: {len(self.steps_failed)}")
        
        if self.steps_completed:
            print("\n✓ Completed:")
            for step in self.steps_completed:
                print(f"  - {step}")
        
        if self.steps_failed:
            print("\n✗ Failed:")
            for step in self.steps_failed:
                print(f"  - {step}")
        
        print("="*60 + "\n")
        
        return len(self.steps_failed) == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Orchestrate Data Lakehouse Pipeline')
    parser.add_argument(
        '--skip-ingestion',
        action='store_true',
        help='Skip data ingestion step'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip dbt tests'
    )
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator()
    success = orchestrator.run_full_pipeline(
        skip_ingestion=args.skip_ingestion,
        run_tests=not args.skip_tests
    )
    
    sys.exit(0 if success else 1)
