-- dbt test: Ensure logical constraints are met
select
    *
from {{ ref('silver_stock_data') }}
where 
    high_price < low_price
    or open_price <= 0
    or close_price <= 0
    or volume < 0
