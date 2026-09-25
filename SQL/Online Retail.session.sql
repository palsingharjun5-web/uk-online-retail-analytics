SELECT
    transaction_type,
    COUNT(*) AS row_count
FROM transactions
GROUP BY transaction_type
ORDER BY row_count DESC;