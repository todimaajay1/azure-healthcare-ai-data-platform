{{
    config(
        materialized='table',
        schema='gold'
    )
}}

-- Gold layer model: Symbol-level summary statistics
-- Aggregated metrics per stock symbol for quick analytics

with silver_data as (
    select
        trade_date,
        symbol,
        open_price,
        close_price,
        high_price,
        low_price,
        volume,
        daily_return_pct
    from {{ ref('silver_stock_data') }}
),

symbol_stats as (
    select
        symbol,
        min(trade_date) as first_trade_date,
        max(trade_date) as last_trade_date,
        count(*) as total_trading_days,
        -- Price statistics
        min(low_price) as all_time_low,
        max(high_price) as all_time_high,
        avg(close_price) as avg_close_price,
        stddev_pop(close_price) as price_std_dev,
        -- Volume statistics
        avg(volume) as avg_volume,
        max(volume) as max_volume,
        min(volume) as min_volume,
        sum(volume) as total_volume,
        -- Return statistics
        avg(daily_return_pct) as avg_daily_return,
        stddev_pop(daily_return_pct) as return_volatility,
        min(daily_return_pct) as worst_daily_return,
        max(daily_return_pct) as best_daily_return,
        -- Calculate total return over period
        (max(close_price) - min(open_price)) / min(open_price) * 100 as total_return_pct,
        current_timestamp as last_updated
    from silver_data
    group by symbol
)

select * from symbol_stats
order by symbol
