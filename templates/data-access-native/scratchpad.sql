-- Returns all customer in country containing 'er', like Germany, Netherlands.
-- This query would not work with Data Server's federated SQL dialect as it's very PostgreSQL specific.
SELECT * FROM public_demo (
    SELECT *
    FROM demo_customers
    WHERE country ~* 'er'
);

-- Try yourself, this won't work:
SELECT *
FROM public_demo.demo_customers
WHERE country ~* 'er';