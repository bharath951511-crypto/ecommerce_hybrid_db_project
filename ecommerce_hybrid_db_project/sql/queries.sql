
INSERT INTO users (first_name, last_name, email, phone, password_hash, role,
                    address_line1, city, state, postal_code, country)
VALUES ('Aisha', 'Khan', 'aisha.khan@example.com', '+91-98765-11111',
        'hash$4f9a2b...', 'customer', '12 MG Road', 'Hyderabad', 'Telangana',
        '500001', 'IN');

START TRANSACTION;
INSERT INTO orders (user_id, status, subtotal_amount, tax_amount, shipping_amount, total_amount)
VALUES (LAST_INSERT_ID(), 'pending', 349.99, 28.00, 0.00, 377.99);
INSERT INTO order_items (order_id, product_id, product_name_snapshot, quantity, unit_price, line_total)
VALUES (LAST_INSERT_ID(), 'P00001', 'Sony Wireless Headphones', 1, 349.99, 349.99);
COMMIT;

SELECT user_id, first_name, last_name, email, city, country, created_at
FROM users
WHERE email = 'aisha.khan@example.com';

SELECT order_id, order_date, status, total_amount
FROM orders
WHERE user_id = 1
ORDER BY order_date DESC;

SELECT o.order_id, o.status AS order_status, o.total_amount,
       oi.product_id, oi.product_name_snapshot, oi.quantity, oi.unit_price,
       p.payment_method, p.status AS payment_status,
       s.carrier, s.tracking_number, s.status AS shipping_status
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
LEFT JOIN payments  p ON p.order_id = o.order_id
LEFT JOIN shipping  s ON s.order_id = o.order_id
WHERE o.order_id = 1;

UPDATE orders SET status = 'shipped' WHERE order_id = 1;

UPDATE inventory
SET stock_quantity = stock_quantity - 1
WHERE product_id = 'P00001' AND warehouse_location = 'Hyderabad-WH1'
  AND stock_quantity >= 1;

UPDATE orders SET status = 'cancelled' WHERE order_id = 5 AND status = 'pending';

SELECT strftime('%Y-%m', order_date) AS month,
       COUNT(*) AS order_count,
       SUM(total_amount) AS revenue
FROM orders
WHERE status NOT IN ('cancelled')
GROUP BY month
ORDER BY month;

SELECT u.user_id, u.first_name, u.last_name, COUNT(o.order_id) AS orders_placed,
       SUM(o.total_amount) AS lifetime_spend
FROM users u
JOIN orders o ON o.user_id = u.user_id
WHERE o.status != 'cancelled'
GROUP BY u.user_id
ORDER BY lifetime_spend DESC
LIMIT 10;

SELECT status, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1) AS pct
FROM orders
GROUP BY status
ORDER BY cnt DESC;

SELECT payment_method,
       COUNT(*) AS attempts,
       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successes,
       ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_pct
FROM payments
GROUP BY payment_method
ORDER BY attempts DESC;

SELECT product_id, warehouse_location, stock_quantity, reorder_level
FROM inventory
WHERE stock_quantity <= reorder_level
ORDER BY stock_quantity ASC;

SELECT AVG(julianday(delivered_date) - julianday(shipped_date)) AS avg_days_to_deliver
FROM shipping
WHERE status = 'delivered';
