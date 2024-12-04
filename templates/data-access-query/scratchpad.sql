-- Get all customers in a country
SELECT company_name, customer_id, account_manager
FROM public_demo.demo_customers
WHERE country = "France"
LIMIT 100;

/* QUERY EXPLAINED

- Only want to see company name, id and account manager
- From postgres database "demo_customers"
- Filter only ones in France
- Only return max 100 results - protecting against too big result sets
*/


-- Get customer's sales per month
SELECT 
    DATE_TRUNC('month', CAST(s.sale_date AS DATE)) as month,
    ROUND(SUM(s.quantity_sold * s.price_per_unit), 2) as total_sales
FROM files.sales_data s
JOIN public_demo.demo_customers c
    ON s.customer_id = c.customer_id
WHERE c.company_name LIKE '%GermanSys%'
GROUP BY DATE_TRUNC('month', CAST(s.sale_date AS DATE))
ORDER BY 1;

/* QUERY EXPLAINED

- Get only month from sales date
- Multiply quantity with price per unit to to get total sales (per month)

- Join sales data from a file, and the customer data from postgres, customer_id being the common nominator
- Filter by customer name, with partial match being ok
- Group by month - we want sales aggregated by month
- Order the months so that earliest is first
*/