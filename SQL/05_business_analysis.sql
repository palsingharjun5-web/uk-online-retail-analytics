/* ============================================================
   UK ONLINE RETAIL
   MASTER BUSINESS ANALYSIS
   SCHEMA-VERIFIED / READ-ONLY
   ============================================================ */


/* ============================================================
   0. DATASET SANITY CHECK
   ============================================================ */

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Sale'
    ) AS sale_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Cancellation'
    ) AS cancellation_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Adjustment / Return'
    ) AS return_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Special / Charge'
    ) AS special_charge_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Zero Price'
    ) AS zero_price_rows,
    COUNT(*) FILTER (
        WHERE transaction_type = 'Bad Debt'
    ) AS bad_debt_rows
FROM transactions;


/* ============================================================
   1. EXECUTIVE KPIs
   ============================================================ */

SELECT
    COUNT(*) AS sales_rows,
    COUNT(DISTINCT invoice) AS total_orders,
    COUNT(DISTINCT customer_id) AS known_customers,
    COUNT(DISTINCT product_id) AS products_sold,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue)::numeric, 2) AS total_revenue,

    ROUND(
        (
            SUM(revenue)
            / NULLIF(COUNT(DISTINCT invoice), 0)
        )::numeric,
        2
    ) AS average_order_value,

    ROUND(
        (
            SUM(revenue)
            / NULLIF(SUM(quantity), 0)
        )::numeric,
        2
    ) AS revenue_per_unit,

    MIN(invoice_date) AS first_sale_date,
    MAX(invoice_date) AS last_sale_date

FROM transactions
WHERE transaction_type = 'Sale';


/* ============================================================
   2. YEARLY PERFORMANCE
   ============================================================ */

SELECT
    year,
    COUNT(DISTINCT invoice) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units,
    ROUND(SUM(revenue)::numeric, 2) AS revenue,

    ROUND(
        (
            100.0
            * SUM(revenue)
            / SUM(SUM(revenue)) OVER ()
        )::numeric,
        2
    ) AS revenue_share_pct

FROM transactions
WHERE transaction_type = 'Sale'

GROUP BY year
ORDER BY year;


/* ============================================================
   3. MONTHLY PERFORMANCE + MONTH-OVER-MONTH GROWTH
   ============================================================ */

WITH monthly AS (
    SELECT
        year_month,
        MIN(invoice_date)::date AS month_start,
        COUNT(DISTINCT invoice) AS orders,
        COUNT(DISTINCT customer_id) AS customers,
        SUM(quantity) AS units,
        SUM(revenue) AS revenue
    FROM transactions
    WHERE transaction_type = 'Sale'
    GROUP BY year_month
)

SELECT
    month_start,
    orders,
    customers,
    units,
    ROUND(revenue::numeric, 2) AS revenue,

    ROUND(
        (
            100.0
            * (
                revenue
                - LAG(revenue) OVER (
                    ORDER BY month_start
                )
            )
            / NULLIF(
                LAG(revenue) OVER (
                    ORDER BY month_start
                ),
                0
            )
        )::numeric,
        2
    ) AS mom_growth_pct

FROM monthly
ORDER BY month_start;


/* ============================================================
   4. SEASONALITY BY CALENDAR MONTH
   ============================================================ */

SELECT
    month,
    month_name,
    COUNT(DISTINCT invoice) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units,
    ROUND(SUM(revenue)::numeric, 2) AS revenue

FROM transactions

WHERE transaction_type = 'Sale'

GROUP BY
    month,
    month_name

ORDER BY month;


/* ============================================================
   5. TOP PRODUCTS BY REVENUE
   ============================================================ */

WITH product_perf AS (
    SELECT
        p.product_id,
        p.stock_code,
        COALESCE(pd.description, 'Unknown') AS description,

        COUNT(DISTINCT t.invoice) AS orders,
        COUNT(DISTINCT t.customer_id) AS customers,
        SUM(t.quantity) AS units,
        SUM(t.revenue) AS revenue

    FROM transactions t

    JOIN products p
        ON t.product_id = p.product_id

    LEFT JOIN product_descriptions pd
        ON t.description_id = pd.description_id

    WHERE t.transaction_type = 'Sale'

    GROUP BY
        p.product_id,
        p.stock_code,
        pd.description
)

SELECT
    stock_code,
    description,
    orders,
    customers,
    units,
    ROUND(revenue::numeric, 2) AS revenue,

    ROUND(
        (
            100.0
            * revenue
            / SUM(revenue) OVER ()
        )::numeric,
        2
    ) AS revenue_share_pct,

    ROUND(
        (
            revenue
            / NULLIF(units, 0)
        )::numeric,
        2
    ) AS revenue_per_unit

FROM product_perf

ORDER BY revenue DESC

LIMIT 20;


/* ============================================================
   6. TOP PRODUCTS BY UNITS
   ============================================================ */

SELECT
    p.stock_code,
    COALESCE(pd.description, 'Unknown') AS description,
    SUM(t.quantity) AS units_sold,
    COUNT(DISTINCT t.invoice) AS orders,
    COUNT(DISTINCT t.customer_id) AS customers,
    ROUND(SUM(t.revenue)::numeric, 2) AS revenue,

    ROUND(
        (
            SUM(t.revenue)
            / NULLIF(SUM(t.quantity), 0)
        )::numeric,
        2
    ) AS revenue_per_unit

FROM transactions t

JOIN products p
    ON t.product_id = p.product_id

LEFT JOIN product_descriptions pd
    ON t.description_id = pd.description_id

WHERE t.transaction_type = 'Sale'

GROUP BY
    p.stock_code,
    pd.description

ORDER BY units_sold DESC

LIMIT 20;


/* ============================================================
   7. HIGH-VOLUME / LOW-REVENUE PRODUCTS
   ============================================================ */

WITH product_perf AS (

    SELECT
        p.stock_code,
        COALESCE(pd.description, 'Unknown') AS description,
        SUM(t.quantity) AS units,
        SUM(t.revenue) AS revenue

    FROM transactions t

    JOIN products p
        ON t.product_id = p.product_id

    LEFT JOIN product_descriptions pd
        ON t.description_id = pd.description_id

    WHERE t.transaction_type = 'Sale'

    GROUP BY
        p.stock_code,
        pd.description
),

ranked AS (

    SELECT
        *,
        NTILE(4) OVER (
            ORDER BY units DESC
        ) AS volume_quartile,

        NTILE(4) OVER (
            ORDER BY revenue DESC
        ) AS revenue_quartile

    FROM product_perf
)

SELECT
    stock_code,
    description,
    units,
    ROUND(revenue::numeric, 2) AS revenue,

    ROUND(
        (
            revenue
            / NULLIF(units, 0)
        )::numeric,
        2
    ) AS revenue_per_unit

FROM ranked

WHERE volume_quartile = 1
  AND revenue_quartile = 4

ORDER BY units DESC

LIMIT 20;


/* ============================================================
   8. TOP CUSTOMERS BY REVENUE
   ============================================================ */

SELECT
    customer_id,
    COUNT(DISTINCT invoice) AS orders,
    SUM(quantity) AS units,
    ROUND(SUM(revenue)::numeric, 2) AS revenue,
    MIN(invoice_date)::date AS first_purchase,
    MAX(invoice_date)::date AS last_purchase,

    ROUND(
        (
            SUM(revenue)
            / NULLIF(COUNT(DISTINCT invoice), 0)
        )::numeric,
        2
    ) AS average_order_value

FROM transactions

WHERE transaction_type = 'Sale'
  AND customer_id IS NOT NULL

GROUP BY customer_id

ORDER BY revenue DESC

LIMIT 20;


/* ============================================================
   9. CUSTOMER ORDER FREQUENCY
   ============================================================ */

WITH customer_orders AS (

    SELECT
        customer_id,
        COUNT(DISTINCT invoice) AS orders

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
)

SELECT
    CASE
        WHEN orders = 1
            THEN '1 order'

        WHEN orders BETWEEN 2 AND 4
            THEN '2-4 orders'

        WHEN orders BETWEEN 5 AND 9
            THEN '5-9 orders'

        WHEN orders BETWEEN 10 AND 19
            THEN '10-19 orders'

        ELSE '20+ orders'
    END AS order_frequency_group,

    COUNT(*) AS customers,

    ROUND(
        (
            100.0
            * COUNT(*)
            / SUM(COUNT(*)) OVER ()
        )::numeric,
        2
    ) AS customer_share_pct

FROM customer_orders

GROUP BY
    CASE
        WHEN orders = 1
            THEN '1 order'
        WHEN orders BETWEEN 2 AND 4
            THEN '2-4 orders'
        WHEN orders BETWEEN 5 AND 9
            THEN '5-9 orders'
        WHEN orders BETWEEN 10 AND 19
            THEN '10-19 orders'
        ELSE '20+ orders'
    END

ORDER BY MIN(orders);


/* ============================================================
   10. REPEAT CUSTOMER RATE
   ============================================================ */

WITH customer_orders AS (

    SELECT
        customer_id,
        COUNT(DISTINCT invoice) AS orders

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
)

SELECT
    COUNT(*) AS known_customers,

    COUNT(*) FILTER (
        WHERE orders = 1
    ) AS one_time_customers,

    COUNT(*) FILTER (
        WHERE orders >= 2
    ) AS repeat_customers,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE orders >= 2
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS repeat_customer_rate_pct

FROM customer_orders;


/* ============================================================
   11. TOP 10 CUSTOMERS REVENUE CONCENTRATION
   ============================================================ */

WITH customer_revenue AS (

    SELECT
        customer_id,
        SUM(revenue) AS revenue

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS rn

    FROM customer_revenue
),

total AS (

    SELECT SUM(revenue) AS total_revenue
    FROM customer_revenue
)

SELECT
    ROUND(
        (
            100.0
            * SUM(r.revenue)
            / NULLIF(t.total_revenue, 0)
        )::numeric,
        2
    ) AS top_10_customer_revenue_share_pct

FROM ranked r

CROSS JOIN total t

WHERE r.rn <= 10

GROUP BY t.total_revenue;


/* ============================================================
   12. COUNTRY PERFORMANCE
   IMPORTANT: COUNTRY IS STORED IN TRANSACTIONS
   ============================================================ */

SELECT
    COALESCE(country, 'Unknown') AS country,

    COUNT(DISTINCT invoice) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units,

    ROUND(SUM(revenue)::numeric, 2) AS revenue,

    ROUND(
        (
            100.0
            * SUM(revenue)
            / SUM(SUM(revenue)) OVER ()
        )::numeric,
        2
    ) AS revenue_share_pct

FROM transactions

WHERE transaction_type = 'Sale'

GROUP BY country

ORDER BY revenue DESC;


/* ============================================================
   13. COUNTRY RETURN ANALYSIS
   ============================================================ */

SELECT
    COALESCE(country, 'Unknown') AS country,

    COUNT(*) AS return_rows,

    COUNT(DISTINCT invoice) AS affected_orders,

    SUM(ABS(quantity)) AS returned_units,

    ROUND(
        SUM(ABS(revenue))::numeric,
        2
    ) AS return_value

FROM transactions

WHERE transaction_type = 'Adjustment / Return'

GROUP BY country

ORDER BY return_value DESC;


/* ============================================================
   14. CANCELLATION + RETURN OVERVIEW
   ============================================================ */

SELECT

    COUNT(*) FILTER (
        WHERE transaction_type = 'Sale'
    ) AS sales_rows,

    COUNT(*) FILTER (
        WHERE transaction_type = 'Cancellation'
    ) AS cancellation_rows,

    COUNT(*) FILTER (
        WHERE transaction_type = 'Adjustment / Return'
    ) AS return_rows,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE transaction_type = 'Cancellation'
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE transaction_type = 'Sale'
                ),
                0
            )
        )::numeric,
        2
    ) AS cancellation_rows_vs_sales_pct,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE transaction_type = 'Adjustment / Return'
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE transaction_type = 'Sale'
                ),
                0
            )
        )::numeric,
        2
    ) AS return_rows_vs_sales_pct,

    ROUND(
        SUM(
            CASE
                WHEN transaction_type = 'Cancellation'
                    THEN ABS(revenue)
                ELSE 0
            END
        )::numeric,
        2
    ) AS cancellation_value,

    ROUND(
        SUM(
            CASE
                WHEN transaction_type = 'Adjustment / Return'
                    THEN ABS(revenue)
                ELSE 0
            END
        )::numeric,
        2
    ) AS return_value

FROM transactions;


/* ============================================================
   15. PRODUCTS WITH RETURN ACTIVITY
   ============================================================ */

WITH product_activity AS (

    SELECT

        p.stock_code,

        COALESCE(
            pd.description,
            'Unknown'
        ) AS description,

        SUM(
            t.quantity
        ) FILTER (
            WHERE t.transaction_type = 'Sale'
        ) AS sold_units,

        SUM(
            t.revenue
        ) FILTER (
            WHERE t.transaction_type = 'Sale'
        ) AS sales_revenue,

        SUM(
            ABS(t.quantity)
        ) FILTER (
            WHERE t.transaction_type = 'Adjustment / Return'
        ) AS returned_units,

        COUNT(*) FILTER (
            WHERE t.transaction_type = 'Adjustment / Return'
        ) AS return_rows

    FROM transactions t

    JOIN products p
        ON t.product_id = p.product_id

    LEFT JOIN product_descriptions pd
        ON t.description_id = pd.description_id

    GROUP BY
        p.stock_code,
        pd.description
)

SELECT

    stock_code,
    description,

    COALESCE(sold_units, 0) AS sold_units,

    ROUND(
        COALESCE(sales_revenue, 0)::numeric,
        2
    ) AS sales_revenue,

    COALESCE(returned_units, 0) AS returned_units,

    COALESCE(return_rows, 0) AS return_rows,

    ROUND(
        (
            100.0
            * COALESCE(returned_units, 0)
            / NULLIF(sold_units, 0)
        )::numeric,
        2
    ) AS unit_return_rate_pct

FROM product_activity

WHERE sold_units > 0
  AND returned_units > 0

ORDER BY unit_return_rate_pct DESC

LIMIT 25;


/* ============================================================
   16. TOP 10 PRODUCTS REVENUE CONCENTRATION
   ============================================================ */

WITH product_revenue AS (

    SELECT
        product_id,
        SUM(revenue) AS revenue

    FROM transactions

    WHERE transaction_type = 'Sale'

    GROUP BY product_id
),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS rn

    FROM product_revenue
),

total AS (

    SELECT SUM(revenue) AS total_revenue
    FROM product_revenue
)

SELECT

    ROUND(
        (
            100.0
            * SUM(r.revenue)
            / NULLIF(t.total_revenue, 0)
        )::numeric,
        2
    ) AS top_10_product_revenue_share_pct

FROM ranked r

CROSS JOIN total t

WHERE r.rn <= 10

GROUP BY t.total_revenue;


/* ============================================================
   17. TOP 5 COUNTRY REVENUE CONCENTRATION
   ============================================================ */

WITH country_revenue AS (

    SELECT
        country,
        SUM(revenue) AS revenue

    FROM transactions

    WHERE transaction_type = 'Sale'

    GROUP BY country
),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS rn

    FROM country_revenue
),

total AS (

    SELECT SUM(revenue) AS total_revenue
    FROM country_revenue
)

SELECT

    ROUND(
        (
            100.0
            * SUM(r.revenue)
            / NULLIF(t.total_revenue, 0)
        )::numeric,
        2
    ) AS top_5_country_revenue_share_pct

FROM ranked r

CROSS JOIN total t

WHERE r.rn <= 5

GROUP BY t.total_revenue;


/* ============================================================
   18. ZERO-PRICE TRANSACTIONS
   ============================================================ */

SELECT

    COUNT(*) AS zero_price_rows,

    COUNT(*) FILTER (
        WHERE quantity > 0
    ) AS positive_quantity_rows,

    COUNT(*) FILTER (
        WHERE quantity < 0
    ) AS negative_quantity_rows,

    SUM(quantity) AS total_units,

    ROUND(
        SUM(revenue)::numeric,
        2
    ) AS revenue_effect

FROM transactions

WHERE transaction_type = 'Zero Price';


/* ============================================================
   19. SPECIAL / CHARGE TRANSACTIONS
   ============================================================ */

SELECT

    p.stock_code,

    COUNT(*) AS rows,

    ROUND(
        SUM(t.revenue)::numeric,
        2
    ) AS transaction_value

FROM transactions t

JOIN products p
    ON t.product_id = p.product_id

WHERE t.transaction_type = 'Special / Charge'

GROUP BY p.stock_code

ORDER BY rows DESC;


/* ============================================================
   20. BAD DEBT
   ============================================================ */

SELECT

    COUNT(*) AS bad_debt_rows,

    ROUND(
        SUM(revenue)::numeric,
        2
    ) AS bad_debt_value

FROM transactions

WHERE transaction_type = 'Bad Debt';


/* ============================================================
   21. CUSTOMER VALUE DISTRIBUTION
   ============================================================ */

WITH customer_revenue AS (

    SELECT
        customer_id,
        SUM(revenue) AS revenue

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
)

SELECT

    ROUND(
        MIN(revenue)::numeric,
        2
    ) AS min_customer_revenue,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY revenue
        )::numeric,
        2
    ) AS p25,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY revenue
        )::numeric,
        2
    ) AS median,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY revenue
        )::numeric,
        2
    ) AS p75,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY revenue
        )::numeric,
        2
    ) AS p90,

    ROUND(
        PERCENTILE_CONT(0.99)
        WITHIN GROUP (
            ORDER BY revenue
        )::numeric,
        2
    ) AS p99,

    ROUND(
        MAX(revenue)::numeric,
        2
    ) AS max_customer_revenue

FROM customer_revenue;


/* ============================================================
   22. ORDER VALUE DISTRIBUTION
   ============================================================ */

WITH order_values AS (

    SELECT
        invoice,
        SUM(revenue) AS order_value

    FROM transactions

    WHERE transaction_type = 'Sale'

    GROUP BY invoice
)

SELECT

    ROUND(
        MIN(order_value)::numeric,
        2
    ) AS min_order_value,

    ROUND(
        PERCENTILE_CONT(0.25)
        WITHIN GROUP (
            ORDER BY order_value
        )::numeric,
        2
    ) AS p25,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY order_value
        )::numeric,
        2
    ) AS median,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY order_value
        )::numeric,
        2
    ) AS p75,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY order_value
        )::numeric,
        2
    ) AS p90,

    ROUND(
        PERCENTILE_CONT(0.99)
        WITHIN GROUP (
            ORDER BY order_value
        )::numeric,
        2
    ) AS p99,

    ROUND(
        MAX(order_value)::numeric,
        2
    ) AS max_order_value

FROM order_values;


/* ============================================================
   23. COHORT RETENTION
   ============================================================ */

WITH first_purchase AS (

    SELECT
        customer_id,
        DATE_TRUNC(
            'month',
            MIN(invoice_date)
        )::date AS cohort_month

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
),

customer_months AS (

    SELECT DISTINCT
        customer_id,
        DATE_TRUNC(
            'month',
            invoice_date
        )::date AS activity_month

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL
),

cohort_activity AS (

    SELECT

        fp.cohort_month,

        cm.activity_month,

        (
            (
                EXTRACT(
                    YEAR FROM cm.activity_month
                )
                -
                EXTRACT(
                    YEAR FROM fp.cohort_month
                )
            ) * 12
            +
            (
                EXTRACT(
                    MONTH FROM cm.activity_month
                )
                -
                EXTRACT(
                    MONTH FROM fp.cohort_month
                )
            )
        )::int AS month_number,

        COUNT(
            DISTINCT cm.customer_id
        ) AS active_customers

    FROM first_purchase fp

    JOIN customer_months cm
        ON fp.customer_id = cm.customer_id

    GROUP BY
        fp.cohort_month,
        cm.activity_month
)

SELECT

    cohort_month,
    month_number,
    active_customers,

    ROUND(
        (
            100.0
            * active_customers
            /
            FIRST_VALUE(
                active_customers
            ) OVER (
                PARTITION BY cohort_month
                ORDER BY month_number
            )
        )::numeric,
        2
    ) AS retention_pct

FROM cohort_activity

WHERE month_number IN (
    0, 1, 3, 6, 12
)

ORDER BY
    cohort_month,
    month_number;


/* ============================================================
   24. CUSTOMER RECENCY
   ============================================================ */

WITH last_purchase AS (

    SELECT

        customer_id,

        MAX(invoice_date)::date
            AS last_purchase_date,

        COUNT(DISTINCT invoice)
            AS orders,

        SUM(revenue)
            AS revenue

    FROM transactions

    WHERE transaction_type = 'Sale'
      AND customer_id IS NOT NULL

    GROUP BY customer_id
),

analysis_end AS (

    SELECT
        MAX(invoice_date)::date AS max_date

    FROM transactions

    WHERE transaction_type = 'Sale'
)

SELECT

    CASE

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 30
            THEN '0-30 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 90
            THEN '31-90 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 180
            THEN '91-180 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 365
            THEN '181-365 days'

        ELSE '365+ days'

    END AS recency_group,

    COUNT(*) AS customers,

    ROUND(
        SUM(lp.revenue)::numeric,
        2
    ) AS revenue

FROM last_purchase lp

CROSS JOIN analysis_end a

GROUP BY

    CASE

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 30
            THEN '0-30 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 90
            THEN '31-90 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 180
            THEN '91-180 days'

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 365
            THEN '181-365 days'

        ELSE '365+ days'

    END

ORDER BY MIN(

    CASE

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 30
            THEN 1

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 90
            THEN 2

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 180
            THEN 3

        WHEN
            (a.max_date - lp.last_purchase_date)
            <= 365
            THEN 4

        ELSE 5

    END
);


/* ============================================================
   25. AUTOMATIC BUSINESS SIGNALS
   ============================================================ */

WITH sales AS (

    SELECT *
    FROM transactions
    WHERE transaction_type = 'Sale'
),

customer_orders AS (

    SELECT
        customer_id,
        COUNT(DISTINCT invoice) AS orders

    FROM sales

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),

customer_revenue AS (

    SELECT
        customer_id,
        SUM(revenue) AS revenue

    FROM sales

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),

product_revenue AS (

    SELECT
        product_id,
        SUM(revenue) AS revenue

    FROM sales

    GROUP BY product_id
),

country_revenue AS (

    SELECT
        country,
        SUM(revenue) AS revenue

    FROM sales

    GROUP BY country
),

total_revenue AS (

    SELECT
        SUM(revenue) AS revenue

    FROM sales
),

top_customer AS (

    SELECT

        ROUND(
            (
                100.0
                * SUM(revenue)
                /
                NULLIF(
                    (
                        SELECT revenue
                        FROM total_revenue
                    ),
                    0
                )
            )::numeric,
            2
        ) AS value

    FROM (

        SELECT revenue

        FROM customer_revenue

        ORDER BY revenue DESC

        LIMIT 10

    ) x
),

top_product AS (

    SELECT

        ROUND(
            (
                100.0
                * SUM(revenue)
                /
                NULLIF(
                    (
                        SELECT revenue
                        FROM total_revenue
                    ),
                    0
                )
            )::numeric,
            2
        ) AS value

    FROM (

        SELECT revenue

        FROM product_revenue

        ORDER BY revenue DESC

        LIMIT 10

    ) x
),

top_country AS (

    SELECT

        ROUND(
            (
                100.0
                * SUM(revenue)
                /
                NULLIF(
                    (
                        SELECT revenue
                        FROM total_revenue
                    ),
                    0
                )
            )::numeric,
            2
        ) AS value

    FROM (

        SELECT revenue

        FROM country_revenue

        ORDER BY revenue DESC

        LIMIT 5

    ) x
),

repeat_rate AS (

    SELECT

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE orders >= 2
                )
                /
                NULLIF(COUNT(*), 0)
            )::numeric,
            2
        ) AS value

    FROM customer_orders
),

return_rate AS (

    SELECT

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE transaction_type
                        = 'Adjustment / Return'
                )
                /
                NULLIF(
                    COUNT(*) FILTER (
                        WHERE transaction_type
                            = 'Sale'
                    ),
                    0
                )
            )::numeric,
            2
        ) AS value

    FROM transactions
)

SELECT
    'Top 10 customers revenue share %' AS metric,
    top_customer.value::text AS value
FROM top_customer

UNION ALL

SELECT
    'Top 10 products revenue share %',
    top_product.value::text
FROM top_product

UNION ALL

SELECT
    'Top 5 countries revenue share %',
    top_country.value::text
FROM top_country

UNION ALL

SELECT
    'Repeat customer rate %',
    repeat_rate.value::text
FROM repeat_rate

UNION ALL

SELECT
    'Return rows vs sales rows %',
    return_rate.value::text
FROM return_rate;