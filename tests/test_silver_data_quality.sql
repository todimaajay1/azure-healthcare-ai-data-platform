-- dbt test: Ensure no null values in critical columns
select
    *
from {{ ref('silver_stock_data') }}
where 
    trade_date is null
    or symbol is null
    or open_price is null
    or high_price is null
    or low_price is null
    or close_price is null
    or volume is null
