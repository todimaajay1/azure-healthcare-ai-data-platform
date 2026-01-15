{{
    config(
        materialized='table',
        schema='gold'
    )
}}

-- Gold layer model: Business-ready aggregated metrics
-- Daily aggregated metrics for analytics and reporting

with silver_data as (
    select
        trade_date,
        symbol,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        daily_range,
        daily_return_pct
    from {{ ref('silver_stock_data') }}
),

daily_metrics as (
    select
        trade_date,
        symbol,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        daily_range,
        daily_return_pct,
        -- Calculate VWAP (Volume Weighted Average Price)
        (high_price + low_price + close_price) / 3 as typical_price,
        (typical_price * volume) as notional_value,
        -- Calculate price volatility indicators
        (high_price - low_price) / close_price as price_volatility_ratio,
        -- Volume metrics
        case 
            when volume > 0 then daily_return_pct / nullif(volume, 0) * 1000000
            else null
        end as return_per_million_volume
    from silver_data
),

aggregated_metrics as (
    select
        trade_date,
        symbol,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        daily_range,
        daily_return_pct,
        typical_price,
        notional_value,
        price_volatility_ratio,
        return_per_million_volume,
        -- Moving averages (for daily context, calculate window functions)
        avg(close_price) over (
            partition by symbol 
            order by trade_date 
            rows between 4 preceding and current row
        ) as ma_5_close,
        avg(close_price) over (
            partition by symbol 
            order by trade_date 
            rows between 9 preceding and current row
        ) as ma_10_close,
        avg(volume) over (
            partition by symbol 
            order by trade_date 
            rows between 9 preceding and current row
        ) as ma_10_volume,
        current_timestamp as gold_timestamp
    from daily_metrics
)

select * from aggregated_metrics
