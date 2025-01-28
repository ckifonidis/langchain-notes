CREATE TABLE bdprod.merchant_promotion_analytical.customer_sector_volumes (
  customer_id STRING,
  sector STRING,
  hyper_category STRING,
  monthly_amount DECIMAL(15,2),
  frequency INT,
  gr_ind BOOLEAN,
  total_wallet DECIMAL(15,2),
  ecommerce_ind BOOLEAN,
  par_ym INT)
PARTITIONED BY (par_ym)
USING delta;
