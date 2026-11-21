-- Move rows older than pivot_epoch from live_orders to hist_orders.
BEGIN;
INSERT INTO hist_orders
SELECT * FROM live_orders
 WHERE created_at < TIMESTAMP 'PIVOT_EPOCH_HERE';
DELETE FROM live_orders
 WHERE created_at < TIMESTAMP 'PIVOT_EPOCH_HERE';
COMMIT;
