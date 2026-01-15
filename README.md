# Enterprise-Grade Data Lakehouse

## Overview

This is an **Enterprise-Grade Data Lakehouse** designed for high-velocity financial analytics, built with modern open-source technologies. The architecture emphasizes scalability, data integrity, and real-time data processing capabilities suitable for production financial data workloads.

The lakehouse implements the **Medallion Architecture** (Bronze → Silver → Gold) to ensure data quality and transformation at each layer, enabling reliable analytics and machine learning use cases.

## Architecture

### Medallion Architecture Layers

1. **Bronze Layer** (`data/bronze/`)
   - Raw, unprocessed data ingested from external sources
   - Stored as Parquet files for efficient columnar storage
   - Preserves all original data without modifications
   - Enables full historical data replay and auditing

2. **Silver Layer** (`data/silver/`)
   - Cleaned and validated data that passed quality checks
   - Data that meets business rules and integrity constraints
   - Ready for downstream transformations and analytics

3. **Gold Layer** (`data/gold/`)
   - Aggregated and business-level datasets
   - Optimized for analytics, reporting, and ML features
   - Contains business-specific transformations and metrics

### Technology Stack

- **DuckDB**: High-performance analytical database for OLAP workloads
- **dbt (Data Build Tool)**: Transformations and data modeling
- **Python**: Data ingestion, quality checks, and orchestration
- **PostgreSQL**: Metadata management and orchestration state
- **Docker**: Containerized infrastructure for consistent deployments
- **Yahoo Finance API**: Real-time financial market data source
- **Parquet**: Efficient columnar storage format

## Project Structure

```
.
├── data/
│   ├── bronze/          # Raw ingested data (Parquet files)
│   ├── silver/          # Validated and cleaned data
│   └── gold/            # Business-ready aggregated data
├── models/
│   ├── staging/         # dbt staging models
│   │   └── stg_stock_data.sql
│   ├── silver/          # dbt silver layer models
│   │   └── silver_stock_data.sql
│   └── gold/            # dbt gold layer models
│       ├── gold_daily_metrics.sql
│       └── gold_symbol_summary.sql
├── tests/               # dbt data quality tests
│   ├── test_silver_data_quality.sql
│   ├── test_logical_constraints.sql
│   └── test_data_freshness.sql
├── src/
│   ├── ingest_data.py      # Data ingestion script
│   ├── data_quality.py     # Quality checks
│   └── orchestrate_pipeline.py  # Full pipeline orchestration
├── dbt_project.yml      # dbt project configuration
├── docker-compose.yml   # PostgreSQL metadata database
├── setup.py             # Setup and installation script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- dbt CLI (optional, can use dbt-duckdb directly)

### Installation

1. **Clone the repository** (or ensure you're in the project directory)

2. **Run setup script** (recommended) or install manually:
   ```bash
   # Automated setup
   python setup.py
   
   # Or manual installation
   pip install -r requirements.txt
   ```

3. **Start the PostgreSQL metadata database:**
   ```bash
   docker-compose up -d
   ```

4. **Verify PostgreSQL is running:**
   ```bash
   docker-compose ps
   ```

### Usage

#### 1. Data Ingestion (Bronze Layer)

Ingest financial market data from Yahoo Finance:

```bash
python src/ingest_data.py
```

This will:
- Fetch stock data for configured symbols (AAPL, GOOGL, MSFT, etc.)
- Save data as Parquet files in `data/bronze/`
- Include metadata such as ingestion timestamp and data source

**Customization:**
- Edit `src/ingest_data.py` to modify symbols, time periods, or intervals
- Default: 1 month of daily data for top 10 stocks

#### 2. Data Quality Checks

Run quality checks before promoting data to Silver:

```bash
python src/data_quality.py
```

Quality checks include:
- **Null Value Validation**: Ensures critical columns (Open, High, Low, Close, Volume, symbol, date) have no nulls
- **Data Type Validation**: Verifies expected data types for numeric columns
- **Logical Range Checks**: Validates High >= Low, prices > 0

#### 3. dbt Transformations

Run dbt models to transform data through the layers:

```bash
# Install dbt-duckdb adapter
pip install dbt-duckdb

# Run all models (staging → silver → gold)
dbt run

# Or run specific layers
dbt run --select staging
dbt run --select silver
dbt run --select gold
```

#### 4. Run Complete Pipeline

Use the orchestration script to run the complete pipeline:

```bash
# Run full pipeline (ingestion → quality → dbt transformations → tests)
python src/orchestrate_pipeline.py

# Skip ingestion if data already exists
python src/orchestrate_pipeline.py --skip-ingestion

# Skip tests
python src/orchestrate_pipeline.py --skip-tests
```

**dbt Models:**

- **Staging** (`models/staging/`):
  - `stg_stock_data.sql`: Reads from bronze layer, performs initial cleaning and standardization

- **Silver** (`models/silver/`):
  - `silver_stock_data.sql`: Cleaned and validated data with deduplication and business rules

- **Gold** (`models/gold/`):
  - `gold_daily_metrics.sql`: Daily aggregated metrics with moving averages and volatility indicators
  - `gold_symbol_summary.sql`: Symbol-level summary statistics for quick analytics

**dbt Tests:**
- Run data quality tests: `dbt test`
- Tests validate null values, logical constraints, and data freshness

### Configuration

#### Database Connection (dbt)

Create a `profiles.yml` file in `~/.dbt/`:

```yaml
data_lakehouse_profile:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: data_lakehouse.duckdb
      schema: main
```

#### Customizing Data Sources

Edit `src/ingest_data.py`:
- Modify `SYMBOLS` list to change stock symbols
- Adjust `PERIOD` for historical data range
- Change `TICKER_INTERVAL` for data granularity (1d, 1h, 1m, etc.)

## Features

### ✅ Data Integrity
- Automated quality checks before data promotion
- Null value detection and validation
- Data type enforcement
- Logical consistency checks

### ✅ Scalability
- Columnar Parquet storage for efficient querying
- DuckDB for high-performance OLAP analytics
- Modular architecture supporting horizontal scaling

### ✅ Real-Time Capabilities
- Configurable ingestion intervals
- Support for high-frequency data (1m, 5m intervals)
- Efficient incremental processing

### ✅ Enterprise-Ready
- Metadata management via PostgreSQL
- Structured logging and error handling
- Version-controlled transformations (dbt)
- Dockerized infrastructure for consistency

## Data Flow

```
Yahoo Finance API
    ↓
[Ingestion Script] → data/bronze/*.parquet (Raw Data)
    ↓
[Quality Checks] → Pass/Fail Validation
    ↓
data/silver/*.parquet (Validated Data)
    ↓
[dbt Transformations] → Staging Models → Aggregations
    ↓
data/gold/ (Business-Ready Datasets)
    ↓
Analytics & ML Applications
```

## Best Practices

1. **Always run quality checks** before promoting data to Silver
2. **Version control** all transformations in dbt models
3. **Monitor ingestion logs** for API errors or data anomalies
4. **Backup metadata database** regularly for production use
5. **Partition Parquet files** by date for better query performance at scale

## Troubleshooting

### PostgreSQL Connection Issues
- Ensure Docker is running: `docker-compose ps`
- Check logs: `docker-compose logs postgres-metadata`
- Verify port 5432 is available

### DuckDB Query Errors
- Ensure Parquet files exist in bronze/silver paths
- Check file permissions
- Verify column names match dbt model expectations

### API Rate Limiting
- Yahoo Finance API may throttle requests
- Add delays between requests in `ingest_data.py` if needed
- Consider using API keys for higher rate limits

## Pipeline Orchestration

The project includes a complete pipeline orchestration script that automates the entire data flow:

```bash
python src/orchestrate_pipeline.py
```

This script:
1. Ingests data to Bronze layer
2. Runs quality checks
3. Executes dbt staging transformations
4. Executes dbt silver transformations  
5. Executes dbt gold transformations
6. Runs dbt data quality tests

All steps are logged with detailed output and error handling.

## Future Enhancements

- [x] Pipeline orchestration script
- [x] Silver and Gold layer dbt models
- [x] Automated data quality tests
- [ ] Dagster orchestration for automated pipelines
- [ ] Airflow/Dagster integration for scheduling
- [ ] Delta Lake format support for ACID transactions
- [ ] Real-time streaming with Kafka/Pulsar
- [ ] ML feature store integration
- [ ] Data catalog and lineage tracking
- [ ] Performance monitoring and alerting

## License

This project is designed for enterprise data engineering use cases.

## Contributing

For production deployments, ensure:
- Proper secrets management (API keys, passwords)
- Environment-specific configurations
- Comprehensive testing of transformations
- Monitoring and alerting setup

---

**Built for Enterprise-Grade Financial Analytics** | High-Velocity Data Processing | Scalable & Reliable
