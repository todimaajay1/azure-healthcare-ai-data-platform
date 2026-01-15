{{
    config(
        materialized='view',
        schema='staging'
    )
}}

-- Staging model that reads from DuckDB bronze layer
-- This model performs initial transformations and data cleaning

with bronze_data as (
    select
        *
    from read_parquet('{{ var("bronze_path") }}/*.parquet', hive_partitioning=0)
),

cleaned_data as (
    select
        -- Standardize date column
        coalesce(date, Date) as trade_date,
        
        -- Ensure symbol is uppercase
        upper(symbol) as symbol,
        
        -- Price columns
        cast(Open as double) as open_price,
        cast(High as double) as high_price,
        cast(Low as double) as low_price,
        cast(Close as double) as close_price,
        
        -- Volume
        cast(Volume as bigint) as volume,
        
        -- Dividends and stock splits
        coalesce(cast(Dividends as double), 0) as dividends,
        coalesce(cast("Stock Splits" as double), 0) as stock_splits,
        
        -- Metadata
        data_source,
        ingestion_timestamp,
        
        -- Calculate additional metrics
        (cast(High as double) - cast(Low as double)) as daily_range,
        ((cast(Close as double) - cast(Open as double)) / cast(Open as double)) * 100 as daily_return_pct
        
    from bronze_data
    
    -- Quality filters: exclude records with null critical fields
    where 
        symbol is not null
        and coalesce(date, Date) is not null
        and Open is not null
        and High is not null
        and Low is not null
        and Close is not null
        and Volume is not null
)

select
    trade_date,
    symbol,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    dividends,
    stock_splits,
    daily_range,
    daily_return_pct,
    data_source,
    ingestion_timestamp,
    current_timestamp as transformed_timestamp
from cleaned_data
