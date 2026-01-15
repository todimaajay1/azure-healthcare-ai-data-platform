{{
    config(
        materialized='table',
        schema='silver'
    )
}}

-- Silver layer model: Cleaned and validated stock data
-- This model reads from validated Parquet files in the silver folder
-- or from staging if silver files don't exist yet

with validated_data as (
    -- Read from staging view (which reads from bronze parquet files)
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
        transformed_timestamp
    from {{ ref('stg_stock_data') }}
),

deduplicated_data as (
    select
        *,
        row_number() over (
            partition by symbol, trade_date 
            order by ingestion_timestamp desc
        ) as row_num
    from validated_data
),

final as (
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
        transformed_timestamp,
        current_timestamp as silver_timestamp
    from deduplicated_data
    where row_num = 1
    -- Additional business rules
    and high_price >= low_price
    and open_price > 0
    and close_price > 0
    and volume >= 0
)

select * from final
