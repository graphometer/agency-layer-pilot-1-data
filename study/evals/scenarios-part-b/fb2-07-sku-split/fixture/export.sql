SELECT id, opened_at, amount_cents, region_tag, sku_code
FROM invoices
GROUP BY {{split}};
