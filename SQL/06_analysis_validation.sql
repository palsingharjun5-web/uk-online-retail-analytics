/* ============================================================
   06 — ANALYSIS VALIDATION
   Targeted checks only
   READ-ONLY
   ============================================================ */


/* ============================================================
   1. CUSTOMER REVENUE COVERAGE + CONCENTRATION
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

all_sales AS (
    SELECT SUM(revenue) AS total_revenue
    FROM transactions
    WHERE transaction_type = 'Sale'
),

known_customer_sales AS (
    SELECT SUM(revenue) AS revenue
    FROM customer_revenue
),

ranked_customers AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS rn
    FROM customer_revenue
)

SELECT
    ROUND(
        known_customer_sales.revenue::numeric,
        2
    ) AS known_customer_revenue,

    ROUND(
        all_sales.total_revenue::numeric,
        2
    ) AS total_sales_revenue,

    ROUND(
        (
            100.0
            * known_customer_sales.revenue
            / NULLIF(all_sales.total_revenue, 0)
        )::numeric,
        2
    ) AS revenue_with_known_customer_pct,

    ROUND(
        (
            100.0
            * SUM(ranked_customers.revenue)
            / NULLIF(known_customer_sales.revenue, 0)
        )::numeric,
        2
    ) AS top_10_customer_share_of_known_customer_revenue

FROM known_customer_sales
CROSS JOIN all_sales
CROSS JOIN ranked_customers
WHERE ranked_customers.rn <= 10
GROUP BY
    known_customer_sales.revenue,
    all_sales.total_revenue;


/* ============================================================
   2. PRODUCT ANALYSIS AT STOCK CODE LEVEL
   Fixes duplicate descriptions
   ============================================================ */

WITH product_perf AS (

    SELECT
        p.stock_code,

        MAX(
            COALESCE(
                pd.description,
                'Unknown'
            )
        ) AS representative_description,

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

    GROUP BY p.stock_code
),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM product_perf
)

SELECT
    stock_code,
    representative_description,
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

FROM ranked

ORDER BY revenue DESC

LIMIT 25;


/* ============================================================
   3. CANCELLATION METRICS
   ============================================================ */

WITH sales AS (

    SELECT
        COUNT(DISTINCT invoice) AS sales_orders,
        SUM(revenue) AS sales_revenue
    FROM transactions
    WHERE transaction_type = 'Sale'
),

cancellations AS (

    SELECT
        COUNT(DISTINCT invoice) AS cancellation_orders,
        SUM(ABS(revenue)) AS cancellation_value
    FROM transactions
    WHERE transaction_type = 'Cancellation'
)

SELECT
    sales.sales_orders,
    cancellations.cancellation_orders,

    ROUND(
        (
            100.0
            * cancellations.cancellation_orders
            / NULLIF(sales.sales_orders, 0)
        )::numeric,
        2
    ) AS cancellation_orders_vs_sales_orders_pct,

    ROUND(
        sales.sales_revenue::numeric,
        2
    ) AS sales_revenue,

    ROUND(
        cancellations.cancellation_value::numeric,
        2
    ) AS cancellation_value,

    ROUND(
        (
            100.0
            * cancellations.cancellation_value
            / NULLIF(sales.sales_revenue, 0)
        )::numeric,
        2
    ) AS cancellation_value_vs_sales_revenue_pct

FROM sales
CROSS JOIN cancellations;


/* ============================================================
   4. WHAT ARE THE "ADJUSTMENT / RETURN" RECORDS?
   ============================================================ */

SELECT

    p.stock_code,

    MAX(
        COALESCE(
            pd.description,
            'Unknown'
        )
    ) AS representative_description,

    COUNT(*) AS adjustment_rows,

    COUNT(DISTINCT t.invoice) AS affected_invoices,

    COUNT(DISTINCT t.customer_id) AS affected_customers,

    SUM(ABS(t.quantity)) AS affected_units,

    MIN(t.price) AS min_price,

    MAX(t.price) AS max_price,

    ROUND(
        SUM(ABS(t.revenue))::numeric,
        2
    ) AS absolute_revenue_value

FROM transactions t

JOIN products p
    ON t.product_id = p.product_id

LEFT JOIN product_descriptions pd
    ON t.description_id = pd.description_id

WHERE t.transaction_type = 'Adjustment / Return'

GROUP BY p.stock_code

ORDER BY affected_units DESC

LIMIT 30;


/* ============================================================
   5. COMPARABLE MONTHLY PERFORMANCE — 2010
   Full calendar year
   ============================================================ */

SELECT

    month AS month_number,

    MAX(month_name) AS month_name,

    COUNT(DISTINCT invoice) AS orders,

    COUNT(DISTINCT customer_id) AS customers,

    SUM(quantity) AS units,

    ROUND(
        SUM(revenue)::numeric,
        2
    ) AS revenue

FROM transactions

WHERE transaction_type = 'Sale'
  AND year = 2010

GROUP BY month

ORDER BY month;


/* ============================================================
   6. 2010 vs 2011 MATCHED-MONTH COMPARISON
   Only Jan-Nov because Dec 2011 is partial
   ============================================================ */

SELECT

    month,

    ROUND(
        SUM(
            CASE
                WHEN year = 2010
                THEN revenue
                ELSE 0
            END
        )::numeric,
        2
    ) AS revenue_2010,

    ROUND(
        SUM(
            CASE
                WHEN year = 2011
                THEN revenue
                ELSE 0
            END
        )::numeric,
        2
    ) AS revenue_2011,

    ROUND(
        (
            100.0
            * (
                SUM(
                    CASE
                        WHEN year = 2011
                        THEN revenue
                        ELSE 0
                    END
                )
                -
                SUM(
                    CASE
                        WHEN year = 2010
                        THEN revenue
                        ELSE 0
                    END
                )
            )
            /
            NULLIF(
                SUM(
                    CASE
                        WHEN year = 2010
                        THEN revenue
                        ELSE 0
                    END
                ),
                0
            )
        )::numeric,
        2
    ) AS yoy_change_pct

FROM transactions

WHERE transaction_type = 'Sale'
  AND year IN (2010, 2011)
  AND month BETWEEN 1 AND 11

GROUP BY month

ORDER BY month;


/* ============================================================
   7. EXTREME QUANTITY TRANSACTIONS
   Investigation only — DO NOT DELETE
   ============================================================ */

SELECT
    t.invoice,
    p.stock_code,
    COALESCE(pd.description, 'Unknown') AS description,
    t.customer_id,
    t.country,
    t.quantity,
    t.price,
    ROUND(t.revenue::numeric, 2) AS revenue,
    t.invoice_date
FROM transactions t
JOIN products p
    ON t.product_id = p.product_id
LEFT JOIN product_descriptions pd
    ON t.description_id = pd.description_id
WHERE t.transaction_type = 'Sale'
ORDER BY t.quantity DESC
LIMIT 30;