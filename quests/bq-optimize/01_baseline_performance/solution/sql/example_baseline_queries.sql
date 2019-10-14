
-- start query 1 in stream 0 using template query96.tpl
select  count(*) 
from tpcds_2t_baseline.store_sales
    ,tpcds_2t_baseline.household_demographics 
    ,tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
where ss_sold_time_sk = time_dim.t_time_sk   
    and ss_hdemo_sk = household_demographics.hd_demo_sk 
    and ss_store_sk = s_store_sk
    and time_dim.t_hour = 8
    and time_dim.t_minute >= 30
    and household_demographics.hd_dep_count = 5
    and store.s_store_name = 'ese'
order by count(*)
limit 100;

-- end query 1 in stream 0 using template query96.tpl
-- start query 2 in stream 0 using template query7.tpl
select  i_item_id, 
        avg(ss_quantity) agg1,
        avg(ss_list_price) agg2,
        avg(ss_coupon_amt) agg3,
        avg(ss_sales_price) agg4 
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.customer_demographics, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.item, tpcds_2t_baseline.promotion
 where ss_sold_date_sk = d_date_sk and
       ss_item_sk = i_item_sk and
       ss_cdemo_sk = cd_demo_sk and
       ss_promo_sk = p_promo_sk and
       cd_gender = 'M' and 
       cd_marital_status = 'M' and
       cd_education_status = '4 yr Degree' and
       (p_channel_email = 'N' or p_channel_event = 'N') and
       d_year = 2001 
 group by i_item_id
 order by i_item_id
 limit 100;

-- end query 2 in stream 0 using template query7.tpl
-- start query 3 in stream 0 using template query75.tpl
WITH all_sales AS (
 SELECT d_year
       ,i_brand_id
       ,i_class_id
       ,i_category_id
       ,i_manufact_id
       ,SUM(sales_cnt) AS sales_cnt
       ,SUM(sales_amt) AS sales_amt
 FROM (SELECT d_year
             ,i_brand_id
             ,i_class_id
             ,i_category_id
             ,i_manufact_id
             ,cs_quantity - COALESCE(cr_return_quantity,0) AS sales_cnt
             ,cs_ext_sales_price - COALESCE(cr_return_amount,0.0) AS sales_amt
       FROM tpcds_2t_baseline.catalog_sales JOIN tpcds_2t_baseline.item ON i_item_sk=cs_item_sk
                          JOIN tpcds_2t_baseline.date_dim ON d_date_sk=cs_sold_date_sk
                          LEFT JOIN tpcds_2t_baseline.catalog_returns ON (cs_order_number=cr_order_number 
                                                    AND cs_item_sk=cr_item_sk)
       WHERE i_category='Shoes'
       UNION ALL
       SELECT d_year
             ,i_brand_id
             ,i_class_id
             ,i_category_id
             ,i_manufact_id
             ,ss_quantity - COALESCE(sr_return_quantity,0) AS sales_cnt
             ,ss_ext_sales_price - COALESCE(sr_return_amt,0.0) AS sales_amt
       FROM tpcds_2t_baseline.store_sales JOIN tpcds_2t_baseline.item ON i_item_sk=ss_item_sk
                        JOIN tpcds_2t_baseline.date_dim ON d_date_sk=ss_sold_date_sk
                        LEFT JOIN tpcds_2t_baseline.store_returns ON (ss_ticket_number=sr_ticket_number 
                                                AND ss_item_sk=sr_item_sk)
       WHERE i_category='Shoes'
       UNION ALL
       SELECT d_year
             ,i_brand_id
             ,i_class_id
             ,i_category_id
             ,i_manufact_id
             ,ws_quantity - COALESCE(wr_return_quantity,0) AS sales_cnt
             ,ws_ext_sales_price - COALESCE(wr_return_amt,0.0) AS sales_amt
       FROM tpcds_2t_baseline.web_sales JOIN tpcds_2t_baseline.item ON i_item_sk=ws_item_sk
                      JOIN tpcds_2t_baseline.date_dim ON d_date_sk=ws_sold_date_sk
                      LEFT JOIN tpcds_2t_baseline.web_returns ON (ws_order_number=wr_order_number 
                                            AND ws_item_sk=wr_item_sk)
       WHERE i_category='Shoes') sales_detail
 GROUP BY d_year, i_brand_id, i_class_id, i_category_id, i_manufact_id)
 SELECT  prev_yr.d_year AS prev_year
                          ,curr_yr.d_year AS year
                          ,curr_yr.i_brand_id
                          ,curr_yr.i_class_id
                          ,curr_yr.i_category_id
                          ,curr_yr.i_manufact_id
                          ,prev_yr.sales_cnt AS prev_yr_cnt
                          ,curr_yr.sales_cnt AS curr_yr_cnt
                          ,curr_yr.sales_cnt-prev_yr.sales_cnt AS sales_cnt_diff
                          ,curr_yr.sales_amt-prev_yr.sales_amt AS sales_amt_diff
 FROM all_sales curr_yr, all_sales prev_yr
 WHERE curr_yr.i_brand_id=prev_yr.i_brand_id
   AND curr_yr.i_class_id=prev_yr.i_class_id
   AND curr_yr.i_category_id=prev_yr.i_category_id
   AND curr_yr.i_manufact_id=prev_yr.i_manufact_id
   AND curr_yr.d_year=2000
   AND prev_yr.d_year=2000-1
   AND CAST(curr_yr.sales_cnt AS NUMERIC)/CAST(prev_yr.sales_cnt AS NUMERIC)<0.9
 ORDER BY sales_cnt_diff,sales_amt_diff
 limit 100;

-- end query 3 in stream 0 using template query75.tpl
-- start query 4 in stream 0 using template query44.tpl
select  asceding.rnk, i1.i_product_name best_performing, i2.i_product_name worst_performing
from(select *
     from (select item_sk,rank() over (order by rank_col asc) rnk
           from (select ss_item_sk item_sk,avg(ss_net_profit) rank_col 
                 from tpcds_2t_baseline.store_sales ss1
                 where ss_store_sk = 20
                 group by ss_item_sk
                 having avg(ss_net_profit) > 0.9*(select avg(ss_net_profit) rank_col
                                                  from tpcds_2t_baseline.store_sales
                                                  where ss_store_sk = 20
                                                    and ss_hdemo_sk is null
                                                  group by ss_store_sk))V1)V11
     where rnk  < 11) asceding,
    (select *
     from (select item_sk,rank() over (order by rank_col desc) rnk
           from (select ss_item_sk item_sk,avg(ss_net_profit) rank_col
                 from tpcds_2t_baseline.store_sales ss1
                 where ss_store_sk = 20
                 group by ss_item_sk
                 having avg(ss_net_profit) > 0.9*(select avg(ss_net_profit) rank_col
                                                  from tpcds_2t_baseline.store_sales
                                                  where ss_store_sk = 20
                                                    and ss_hdemo_sk is null
                                                  group by ss_store_sk))V2)V21
     where rnk  < 11) descending,
tpcds_2t_baseline.item i1,
tpcds_2t_baseline.item i2
where asceding.rnk = descending.rnk 
  and i1.i_item_sk=asceding.item_sk
  and i2.i_item_sk=descending.item_sk
order by asceding.rnk
limit 100;
 
 -- END OF BENCHMARK