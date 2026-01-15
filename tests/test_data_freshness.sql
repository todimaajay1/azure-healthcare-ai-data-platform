-- dbt test: Ensure data is relatively fresh (within last 7 days)
-- This test will warn if data is stale
select
    symbol,
    max(trade_date) as latest_trade_date,
    datediff('day', max(trade_date), current_date) as days_since_last_trade
from {{ ref('silver_stock_data') }}
group by symbol
having datediff('day', max(trade_date), current_date) > 7
