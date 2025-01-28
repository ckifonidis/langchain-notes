# Databricks notebook source
# DBTITLE 1,Load Generics Notebook
%run ./Generics

# COMMAND ----------
# DBTITLE 1,Parse Workflow Parameters
catalog = get_catalog()
parym_range = get_parym_range_condition()
(pardt1, pardt2) = get_pardt_integer_range()
parym_end = extract_parym(pardt2)

# COMMAND ----------
# DBTITLE 1,Build Query

query = f"""
INSERT INTO {catalog}.merchant_promotion_analytical.cards_customer_characteristics 
REPLACE WHERE {parym_range}
with all_comb as (
  select
    cast (date_format(ts, 'yyyyMM') as int) as par_ym,
    cast(date_format(ts - interval 12 months, 'yyyyMM') as int) as par_ym_year_before
  from (
    select
      explode(sequence(to_timestamp(cast({pardt1} as string), 'yyyyMMdd'), to_timestamp(cast({pardt2} as string), 'yyyyMMdd'), interval 1 month)) as ts
  )
),
customer_data AS (
    SELECT/*+ RANGE_JOIN(v, 1) */
        ac.par_ym,
        customer_id,
        hyper_category,
        SUM(monthly_amount) AS customer_amount
    FROM
    {catalog}.merchant_promotion_analytical.customer_sector_volumes v join
    all_comb ac 
    on v.par_ym between ac.par_ym_year_before and ac.par_ym
    WHERE v.par_ym between cast(date_format(to_timestamp(cast({pardt1} as string), 'yyyyMMdd') - interval 12 months, 'yyyyMM') as int) and {parym_end}
    GROUP BY ac.par_ym, customer_id, hyper_category
),

customer_sector_share AS (
    SELECT
        par_ym,
        customer_id,
        hyper_category,
        ROUND((customer_amount/(SUM(customer_amount) over (partition by par_ym, customer_id))) *100, 2) AS perc_share
    FROM customer_data
),
hypercategory_mapping as (
    select  distinct hyper_category, sector from {catalog}.merchant_promotion_core.mcc_categories where sector is not null
),
interests AS (
    SELECT /*+ BROADCASTJOIN(h) */
        c.par_ym,
        c.customer_id,
        h.sector as shopping_interests
    FROM
        customer_sector_share c
        join hypercategory_mapping h
        on c.hyper_category = h.hyper_category
    QUALIFY c.perc_share > (ROUND(AVG(perc_share) over (partition by c.par_ym, c.hyper_category), 2))
)
SELECT /*+ BROADCASTJOIN(h, w) */ DISTINCT
{parym_end} as par_ym,
c.customer_id,
c.age,
c.home_location,
h.municipality as home_municipality,
h.regional_unit as home_regional_unit,
h.region as home_region,
c.work_location,
w.municipality as work_municipality,
w.regional_unit as work_regional_unit,
w.region as work_region,
c.gender,
c.occupation,
c.annual_income,
c.nbg_segment,
c.sms_ind,
c.email_ind,
c.addr_ind,
c.memberships,
c.ibank_ind,
i.shopping_interests,
c.age_range_cat
FROM {catalog}.merchant_promotion_core.customer c
LEFT JOIN interests i
ON c.customer_id = i.customer_id
LEFT JOIN {catalog}.merchant_promotion_core.postal_codes h
ON c.home_location = h.postal
LEFT JOIN {catalog}.merchant_promotion_core.postal_codes w
ON c.work_location = w.postal
  """

# COMMAND ----------
# DBTITLE 1,Print update query
print(query)

# COMMAND ----------
# DBTITLE 1,Update the table with insights data
if (not exclude_analytical_computations()) and generic_update():
    display(spark.sql(query))


# COMMAND ----------
# DBTITLE 1,Optimize the table
optimizeQuery = f"""
OPTIMIZE {catalog}.merchant_promotion_analytical.cards_customer_characteristics 
WHERE {parym_range}
zorder by (customer_id, shopping_interests)
"""

print(optimizeQuery)

# COMMAND ----------
# DBTITLE 1,Optimize the table
if (not exclude_analytical_computations()) and generic_update():
    display(spark.sql(optimizeQuery))


