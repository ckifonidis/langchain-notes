CREATE TABLE bdprod.merchant_promotion_core.customer (
  customer_id STRING,
  age INT,
  home_location STRING,
  work_location STRING,
  gender STRING,
  occupation STRING,
  annual_income DECIMAL(15,2),
  nbg_segment STRING,
  sms_ind BOOLEAN,
  email_ind BOOLEAN,
  addr_ind BOOLEAN,
  memberships ARRAY<STRING>,
  ibank_ind BOOLEAN,
  age_range_cat INT
)
USING DELTA 
PARTITIONED BY (age_range_cat)
