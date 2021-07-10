
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

-- end query 4 in stream 0 using template query44.tpl
-- start query 5 in stream 0 using template query39.tpl
with inv as
(select w_warehouse_name,w_warehouse_sk,i_item_sk,d_moy
       ,stdev,mean, case mean when 0 then null else stdev/mean end cov
 from(select w_warehouse_name,w_warehouse_sk,i_item_sk,d_moy
            ,stddev_samp(inv_quantity_on_hand) stdev,avg(inv_quantity_on_hand) mean
      from tpcds_2t_baseline.inventory
          ,tpcds_2t_baseline.item
          ,tpcds_2t_baseline.warehouse
          ,tpcds_2t_baseline.date_dim
      where inv_item_sk = i_item_sk
        and inv_warehouse_sk = w_warehouse_sk
        and inv_date_sk = d_date_sk
        and d_year =2001
      group by w_warehouse_name,w_warehouse_sk,i_item_sk,d_moy) foo
 where case mean when 0 then 0 else stdev/mean end > 1)
select inv1.w_warehouse_sk as inv1_w_warehouse_sk,inv1.i_item_sk as inv1_i_item_sk, inv1.d_moy as inv1_d_moy, inv1.mean as inv1_mean, inv1.cov as inv1_cov
        ,inv2.w_warehouse_sk as inv2_w_warehouse_sk,inv2.i_item_sk as inv2_i_item_sk, inv2.d_moy as inv2_d_moy,inv2.mean as inv2_mean, inv2.cov as inv2_cov
from inv inv1,inv inv2
where inv1.i_item_sk = inv2.i_item_sk
  and inv1.w_warehouse_sk =  inv2.w_warehouse_sk
  and inv1.d_moy=1
  and inv2.d_moy=1+1
  and inv1.cov > 1.5
order by inv1.w_warehouse_sk,inv1.i_item_sk,inv1.d_moy,inv1.mean,inv1.cov
        ,inv2.d_moy,inv2.mean, inv2.cov
;

-- end query 5 in stream 0 using template query39.tpl
-- start query 6 in stream 0 using template query80.tpl
with ssr as
 (select  s_store_id as store_id,
          sum(ss_ext_sales_price) as sales,
          sum(coalesce(sr_return_amt, 0)) as returns,
          sum(ss_net_profit - coalesce(sr_net_loss, 0)) as profit
  from tpcds_2t_baseline.store_sales left outer join tpcds_2t_baseline.store_returns on
         (ss_item_sk = sr_item_sk and ss_ticket_number = sr_ticket_number),
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.store,
     tpcds_2t_baseline.item,
     tpcds_2t_baseline.promotion
 where ss_sold_date_sk = d_date_sk
       and d_date between date(2002, 08, 04) 
           and date_add(date '2002-08-04', interval 30 day)
       and ss_store_sk = s_store_sk
       and ss_item_sk = i_item_sk
       and i_current_price > 50
       and ss_promo_sk = p_promo_sk
       and p_channel_tv = 'N'
 group by s_store_id)
 ,
 csr as
 (select  cp_catalog_page_id as catalog_page_id,
          sum(cs_ext_sales_price) as sales,
          sum(coalesce(cr_return_amount, 0)) as returns,
          sum(cs_net_profit - coalesce(cr_net_loss, 0)) as profit
  from tpcds_2t_baseline.catalog_sales left outer join tpcds_2t_baseline.catalog_returns on
         (cs_item_sk = cr_item_sk and cs_order_number = cr_order_number),
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.catalog_page,
     tpcds_2t_baseline.item,
     tpcds_2t_baseline.promotion
 where cs_sold_date_sk = d_date_sk
       and d_date between date(2002, 08, 04) 
           and date_add(date '2002-08-04', interval 30 day)
       and cs_catalog_page_sk = cp_catalog_page_sk
       and cs_item_sk = i_item_sk
       and i_current_price > 50
       and cs_promo_sk = p_promo_sk
       and p_channel_tv = 'N'
group by cp_catalog_page_id)
 ,
 wsr as
 (select  web_site_id,
          sum(ws_ext_sales_price) as sales,
          sum(coalesce(wr_return_amt, 0)) as returns,
          sum(ws_net_profit - coalesce(wr_net_loss, 0)) as profit
  from tpcds_2t_baseline.web_sales left outer join tpcds_2t_baseline.web_returns on
         (ws_item_sk = wr_item_sk and ws_order_number = wr_order_number),
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.web_site,
     tpcds_2t_baseline.item,
     tpcds_2t_baseline.promotion
 where ws_sold_date_sk = d_date_sk
       and d_date between date(2002, 08, 04) 
       and date_add(date '2002-08-04', interval 30 day)
       and ws_web_site_sk = web_site_sk
       and ws_item_sk = i_item_sk
       and i_current_price > 50
       and ws_promo_sk = p_promo_sk
       and p_channel_tv = 'N'
group by web_site_id)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , concat('store', store_id) as id
        , sales
        , returns
        , profit
 from   ssr
 union all
 select 'catalog channel' as channel
        , concat('catalog_page', catalog_page_id) as id
        , sales
        , returns
        , profit
 from  csr
 union all
 select 'web channel' as channel
        , concat('web_site', web_site_id) as id
        , sales
        , returns
        , profit
 from   wsr
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;

-- end query 6 in stream 0 using template query80.tpl
-- start query 7 in stream 0 using template query32.tpl
select  sum(cs_ext_discount_amt)  as excess_discount_amount 
from 
   tpcds_2t_baseline.catalog_sales 
   ,tpcds_2t_baseline.item 
   ,tpcds_2t_baseline.date_dim
where
i_manufact_id = 283
and i_item_sk = cs_item_sk 
and d_date between date(1999, 02, 22) and 
        date_add(DATE '1999-02-22', interval 90 day)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            tpcds_2t_baseline.catalog_sales 
           ,tpcds_2t_baseline.date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between date(1999, 02, 22) and
                 date_add(DATE '1999-02-22', interval 90 day)
          and d_date_sk = cs_sold_date_sk 
      ) 
limit 100;

-- end query 7 in stream 0 using template query32.tpl
-- start query 8 in stream 0 using template query19.tpl
select  i_brand_id brand_id, i_brand brand, i_manufact_id, i_manufact,
 	sum(ss_ext_sales_price) ext_price
 from tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.item,tpcds_2t_baseline.customer,tpcds_2t_baseline.customer_address,tpcds_2t_baseline.store
 where d_date_sk = ss_sold_date_sk
   and ss_item_sk = i_item_sk
   and i_manager_id=8
   and d_moy=11
   and d_year=1999
   and ss_customer_sk = c_customer_sk 
   and c_current_addr_sk = ca_address_sk
   and substr(ca_zip,1,5) <> substr(s_zip,1,5) 
   and ss_store_sk = s_store_sk 
 group by i_brand
      ,i_brand_id
      ,i_manufact_id
      ,i_manufact
 order by ext_price desc
         ,i_brand
         ,i_brand_id
         ,i_manufact_id
         ,i_manufact
limit 100 ;

-- end query 8 in stream 0 using template query19.tpl
-- start query 9 in stream 0 using template query25.tpl
select  
 i_item_id
 ,i_item_desc
 ,s_store_id
 ,s_store_name
 ,min(ss_net_profit) as store_sales_profit
 ,min(sr_net_loss) as store_returns_loss
 ,min(cs_net_profit) as catalog_sales_profit
 from
 tpcds_2t_baseline.store_sales
 ,tpcds_2t_baseline.store_returns
 ,tpcds_2t_baseline.catalog_sales
 ,tpcds_2t_baseline.date_dim d1
 ,tpcds_2t_baseline.date_dim d2
 ,tpcds_2t_baseline.date_dim d3
 ,tpcds_2t_baseline.store
 ,tpcds_2t_baseline.item
 where
 d1.d_moy = 4
 and d1.d_year = 2002
 and d1.d_date_sk = ss_sold_date_sk
 and i_item_sk = ss_item_sk
 and s_store_sk = ss_store_sk
 and ss_customer_sk = sr_customer_sk
 and ss_item_sk = sr_item_sk
 and ss_ticket_number = sr_ticket_number
 and sr_returned_date_sk = d2.d_date_sk
 and d2.d_moy               between 4 and  10
 and d2.d_year              = 2002
 and sr_customer_sk = cs_bill_customer_sk
 and sr_item_sk = cs_item_sk
 and cs_sold_date_sk = d3.d_date_sk
 and d3.d_moy               between 4 and  10 
 and d3.d_year              = 2002
 group by
 i_item_id
 ,i_item_desc
 ,s_store_id
 ,s_store_name
 order by
 i_item_id
 ,i_item_desc
 ,s_store_id
 ,s_store_name
 limit 100;

-- end query 9 in stream 0 using template query25.tpl
-- start query 10 in stream 0 using template query78.tpl
with ws as
  (select d_year AS ws_sold_year, ws_item_sk,
    ws_bill_customer_sk ws_customer_sk,
    sum(ws_quantity) ws_qty,
    sum(ws_wholesale_cost) ws_wc,
    sum(ws_sales_price) ws_sp
   from tpcds_2t_baseline.web_sales
   left join tpcds_2t_baseline.web_returns on wr_order_number=ws_order_number and ws_item_sk=wr_item_sk
   join tpcds_2t_baseline.date_dim on ws_sold_date_sk = d_date_sk
   where wr_order_number is null
   group by d_year, ws_item_sk, ws_bill_customer_sk
   ),
cs as
  (select d_year AS cs_sold_year, cs_item_sk,
    cs_bill_customer_sk cs_customer_sk,
    sum(cs_quantity) cs_qty,
    sum(cs_wholesale_cost) cs_wc,
    sum(cs_sales_price) cs_sp
   from tpcds_2t_baseline.catalog_sales
   left join tpcds_2t_baseline.catalog_returns on cr_order_number=cs_order_number and cs_item_sk=cr_item_sk
   join tpcds_2t_baseline.date_dim on cs_sold_date_sk = d_date_sk
   where cr_order_number is null
   group by d_year, cs_item_sk, cs_bill_customer_sk
   ),
ss as
  (select d_year AS ss_sold_year, ss_item_sk,
    ss_customer_sk,
    sum(ss_quantity) ss_qty,
    sum(ss_wholesale_cost) ss_wc,
    sum(ss_sales_price) ss_sp
   from tpcds_2t_baseline.store_sales
   left join tpcds_2t_baseline.store_returns on sr_ticket_number=ss_ticket_number and ss_item_sk=sr_item_sk
   join tpcds_2t_baseline.date_dim on ss_sold_date_sk = d_date_sk
   where sr_ticket_number is null
   group by d_year, ss_item_sk, ss_customer_sk
   )
 select 
ss_customer_sk,
round(ss_qty/(coalesce(ws_qty,0)+coalesce(cs_qty,0)),2) ratio,
ss_qty store_qty, ss_wc store_wholesale_cost, ss_sp store_sales_price,
coalesce(ws_qty,0)+coalesce(cs_qty,0) other_chan_qty,
coalesce(ws_wc,0)+coalesce(cs_wc,0) other_chan_wholesale_cost,
coalesce(ws_sp,0)+coalesce(cs_sp,0) other_chan_sales_price
from ss
left join ws on (ws_sold_year=ss_sold_year and ws_item_sk=ss_item_sk and ws_customer_sk=ss_customer_sk)
left join cs on (cs_sold_year=ss_sold_year and cs_item_sk=ss_item_sk and cs_customer_sk=ss_customer_sk)
where (coalesce(ws_qty,0)>0 or coalesce(cs_qty, 0)>0) and ss_sold_year=2001
order by 
  ss_customer_sk,
  ss_qty desc, ss_wc desc, ss_sp desc,
  other_chan_qty,
  other_chan_wholesale_cost,
  other_chan_sales_price,
  ratio
limit 100;

-- end query 10 in stream 0 using template query78.tpl
-- start query 11 in stream 0 using template query86.tpl
select   
    sum(ws_net_paid) as total_sum
   ,i_category
   ,i_class
   ,concat(i_category, i_class) as lochierarchy
   ,rank() over (
 	partition by concat(i_category, i_class),
 	case when i_class = '0' then i_category end 
 	order by sum(ws_net_paid) desc) as rank_within_parent
 from
    tpcds_2t_baseline.web_sales
   ,tpcds_2t_baseline.date_dim       d1
   ,tpcds_2t_baseline.item
 where
    d1.d_month_seq between 1205 and 1205+11
 and d1.d_date_sk = ws_sold_date_sk
 and i_item_sk  = ws_item_sk
 group by rollup(i_category,i_class)
 order by
   lochierarchy desc,
   case when lochierarchy = '0' then i_category end,
   rank_within_parent
 limit 100;

-- end query 11 in stream 0 using template query86.tpl
-- start query 12 in stream 0 using template query1.tpl
with customer_total_return as
(select sr_customer_sk as ctr_customer_sk
,sr_store_sk as ctr_store_sk
,sum(SR_RETURN_AMT_INC_TAX) as ctr_total_return
from tpcds_2t_baseline.store_returns
,tpcds_2t_baseline.date_dim
where sr_returned_date_sk = d_date_sk
and d_year =1999
group by sr_customer_sk
,sr_store_sk)
 select  c_customer_id
from customer_total_return ctr1
,tpcds_2t_baseline.store
,tpcds_2t_baseline.customer
where ctr1.ctr_total_return > (select avg(ctr_total_return)*1.2
from customer_total_return ctr2
where ctr1.ctr_store_sk = ctr2.ctr_store_sk)
and s_store_sk = ctr1.ctr_store_sk
and s_state = 'SD'
and ctr1.ctr_customer_sk = c_customer_sk
order by c_customer_id
limit 100;

-- end query 12 in stream 0 using template query1.tpl
-- start query 13 in stream 0 using template query91.tpl
select  
        cc_call_center_id Call_Center,
        cc_name Call_Center_Name,
        cc_manager Manager,
        sum(cr_net_loss) Returns_Loss
from
        tpcds_2t_baseline.call_center,
        tpcds_2t_baseline.catalog_returns,
        tpcds_2t_baseline.date_dim,
        tpcds_2t_baseline.customer,
        tpcds_2t_baseline.customer_address,
        tpcds_2t_baseline.customer_demographics,
        tpcds_2t_baseline.household_demographics
where
        cr_call_center_sk       = cc_call_center_sk
and     cr_returned_date_sk     = d_date_sk
and     cr_returning_customer_sk= c_customer_sk
and     cd_demo_sk              = c_current_cdemo_sk
and     hd_demo_sk              = c_current_hdemo_sk
and     ca_address_sk           = c_current_addr_sk
and     d_year                  = 2002 
and     d_moy                   = 11
and     ( (cd_marital_status       = 'M' and cd_education_status     = 'Unknown')
        or(cd_marital_status       = 'W' and cd_education_status     = 'Advanced Degree'))
and     hd_buy_potential like 'Unknown%'
and     ca_gmt_offset           = -6
group by cc_call_center_id,cc_name,cc_manager,cd_marital_status,cd_education_status
order by sum(cr_net_loss) desc;

-- end query 13 in stream 0 using template query91.tpl
-- start query 14 in stream 0 using template query21.tpl
select  *
 from(select w_warehouse_name
            ,i_item_id
            ,sum(case when (cast(d_date as date) < cast ('2000-05-19' as date))
	                then inv_quantity_on_hand 
                      else 0 end) as inv_before
            ,sum(case when (cast(d_date as date) >= cast ('2000-05-19' as date))
                      then inv_quantity_on_hand 
                      else 0 end) as inv_after
   from tpcds_2t_baseline.inventory
       ,tpcds_2t_baseline.warehouse
       ,tpcds_2t_baseline.item
       ,tpcds_2t_baseline.date_dim
   where i_current_price between 0.99 and 1.49
     and i_item_sk          = inv_item_sk
     and inv_warehouse_sk   = w_warehouse_sk
     and inv_date_sk    = d_date_sk
     and d_date between date_sub(date '2000-05-19', interval 30 day)
                    and date_add(date '2000-05-19', interval 30 day)
   group by w_warehouse_name, i_item_id) x
 where (case when inv_before > 0 
             then inv_after / inv_before 
             else null
             end) between 2.0/3.0 and 3.0/2.0
 order by w_warehouse_name
         ,i_item_id
 limit 100;

-- end query 14 in stream 0 using template query21.tpl
-- start query 15 in stream 0 using template query43.tpl
select  s_store_name, s_store_id,
        sum(case when (d_day_name='Sunday') then ss_sales_price else null end) sun_sales,
        sum(case when (d_day_name='Monday') then ss_sales_price else null end) mon_sales,
        sum(case when (d_day_name='Tuesday') then ss_sales_price else  null end) tue_sales,
        sum(case when (d_day_name='Wednesday') then ss_sales_price else null end) wed_sales,
        sum(case when (d_day_name='Thursday') then ss_sales_price else null end) thu_sales,
        sum(case when (d_day_name='Friday') then ss_sales_price else null end) fri_sales,
        sum(case when (d_day_name='Saturday') then ss_sales_price else null end) sat_sales
 from tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.store
 where d_date_sk = ss_sold_date_sk and
       s_store_sk = ss_store_sk and
       s_gmt_offset = -5 and
       d_year = 2000 
 group by s_store_name, s_store_id
 order by s_store_name, s_store_id,sun_sales,mon_sales,tue_sales,wed_sales,thu_sales,fri_sales,sat_sales
 limit 100;

-- end query 15 in stream 0 using template query43.tpl
-- start query 16 in stream 0 using template query27.tpl
select  i_item_id,
        s_state, s_state as g_state,
        avg(ss_quantity) agg1,
        avg(ss_list_price) agg2,
        avg(ss_coupon_amt) agg3,
        avg(ss_sales_price) agg4
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.customer_demographics, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store, tpcds_2t_baseline.item
 where ss_sold_date_sk = d_date_sk and
       ss_item_sk = i_item_sk and
       ss_store_sk = s_store_sk and
       ss_cdemo_sk = cd_demo_sk and
       cd_gender = 'F' and
       cd_marital_status = 'D' and
       cd_education_status = 'College' and
       d_year = 2002 and
       s_state in ('SD','AL', 'TN', 'SD', 'SD', 'SD')
 group by rollup (i_item_id, s_state)
 order by i_item_id
         ,s_state
 limit 100;

-- end query 16 in stream 0 using template query27.tpl
-- start query 17 in stream 0 using template query94.tpl
select  
   count(distinct ws_order_number) as order_count
  ,sum(ws_ext_ship_cost) as total_shipping_cost
  ,sum(ws_net_profit) as total_net_profit
from
   tpcds_2t_baseline.web_sales ws1
  ,tpcds_2t_baseline.date_dim
  ,tpcds_2t_baseline.customer_address
  ,tpcds_2t_baseline.web_site
where
    d_date between '2001-5-01' and 
           date_add(date '2001-5-01', interval 60 day)
and ws1.ws_ship_date_sk = d_date_sk
and ws1.ws_ship_addr_sk = ca_address_sk
and ca_state = 'AR'
and ws1.ws_web_site_sk = web_site_sk
and web_company_name = 'pri'
and exists (select *
            from tpcds_2t_baseline.web_sales ws2
            where ws1.ws_order_number = ws2.ws_order_number
              and ws1.ws_warehouse_sk <> ws2.ws_warehouse_sk)
and not exists(select *
               from tpcds_2t_baseline.web_returns wr1
               where ws1.ws_order_number = wr1.wr_order_number)
order by count(distinct ws_order_number)
limit 100;

-- end query 17 in stream 0 using template query94.tpl
-- start query 18 in stream 0 using template query45.tpl
select  ca_zip, ca_county, sum(ws_sales_price)
 from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.customer, tpcds_2t_baseline.customer_address, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.item
 where ws_bill_customer_sk = c_customer_sk
 	and c_current_addr_sk = ca_address_sk 
 	and ws_item_sk = i_item_sk 
 	and ( substr(ca_zip,1,5) in ('85669', '86197','88274','83405','86475', '85392', '85460', '80348', '81792')
 	      or 
 	      i_item_id in (select i_item_id
                             from tpcds_2t_baseline.item
                             where i_item_sk in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
                             )
 	    )
 	and ws_sold_date_sk = d_date_sk
 	and d_qoy = 2 and d_year = 2000
 group by ca_zip, ca_county
 order by ca_zip, ca_county
 limit 100;

-- end query 18 in stream 0 using template query45.tpl
-- start query 19 in stream 0 using template query58.tpl
with ss_items as
 (select i_item_id item_id
        ,sum(ss_ext_sales_price) ss_item_rev 
 from tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.item
     ,tpcds_2t_baseline.date_dim
 where ss_item_sk = i_item_sk
   and d_date in (select d_date
                  from tpcds_2t_baseline.date_dim
                  where d_week_seq = (select d_week_seq 
                                      from tpcds_2t_baseline.date_dim
                                      where d_date = '1998-02-19'))
   and ss_sold_date_sk   = d_date_sk
 group by i_item_id),
 cs_items as
 (select i_item_id item_id
        ,sum(cs_ext_sales_price) cs_item_rev
  from tpcds_2t_baseline.catalog_sales
      ,tpcds_2t_baseline.item
      ,tpcds_2t_baseline.date_dim
 where cs_item_sk = i_item_sk
  and  d_date in (select d_date
                  from tpcds_2t_baseline.date_dim
                  where d_week_seq = (select d_week_seq 
                                      from tpcds_2t_baseline.date_dim
                                      where d_date = '1998-02-19'))
  and  cs_sold_date_sk = d_date_sk
 group by i_item_id),
 ws_items as
 (select i_item_id item_id
        ,sum(ws_ext_sales_price) ws_item_rev
  from tpcds_2t_baseline.web_sales
      ,tpcds_2t_baseline.item
      ,tpcds_2t_baseline.date_dim
 where ws_item_sk = i_item_sk
  and  d_date in (select d_date
                  from tpcds_2t_baseline.date_dim
                  where d_week_seq =(select d_week_seq 
                                     from tpcds_2t_baseline.date_dim
                                     where d_date = '1998-02-19'))
  and ws_sold_date_sk   = d_date_sk
 group by i_item_id)
  select  ss_items.item_id
       ,ss_item_rev
       ,ss_item_rev/((ss_item_rev+cs_item_rev+ws_item_rev)/3) * 100 ss_dev
       ,cs_item_rev
       ,cs_item_rev/((ss_item_rev+cs_item_rev+ws_item_rev)/3) * 100 cs_dev
       ,ws_item_rev
       ,ws_item_rev/((ss_item_rev+cs_item_rev+ws_item_rev)/3) * 100 ws_dev
       ,(ss_item_rev+cs_item_rev+ws_item_rev)/3 average
 from ss_items,cs_items,ws_items
 where ss_items.item_id=cs_items.item_id
   and ss_items.item_id=ws_items.item_id 
   and ss_item_rev between 0.9 * cs_item_rev and 1.1 * cs_item_rev
   and ss_item_rev between 0.9 * ws_item_rev and 1.1 * ws_item_rev
   and cs_item_rev between 0.9 * ss_item_rev and 1.1 * ss_item_rev
   and cs_item_rev between 0.9 * ws_item_rev and 1.1 * ws_item_rev
   and ws_item_rev between 0.9 * ss_item_rev and 1.1 * ss_item_rev
   and ws_item_rev between 0.9 * cs_item_rev and 1.1 * cs_item_rev
 order by item_id
         ,ss_item_rev
 limit 100;

-- end query 19 in stream 0 using template query58.tpl
-- start query 20 in stream 0 using template query64.tpl
with cs_ui as
 (select cs_item_sk
        ,sum(cs_ext_list_price) as sale,sum(cr_refunded_cash+cr_reversed_charge+cr_store_credit) as refund
  from tpcds_2t_baseline.catalog_sales
      ,tpcds_2t_baseline.catalog_returns
  where cs_item_sk = cr_item_sk
    and cs_order_number = cr_order_number
  group by cs_item_sk
  having sum(cs_ext_list_price)>2*sum(cr_refunded_cash+cr_reversed_charge+cr_store_credit)),
cross_sales as
 (select i_product_name product_name
     ,i_item_sk item_sk
     ,s_store_name store_name
     ,s_zip store_zip
     ,ad1.ca_street_number b_street_number
     ,ad1.ca_street_name b_street_name
     ,ad1.ca_city b_city
     ,ad1.ca_zip b_zip
     ,ad2.ca_street_number c_street_number
     ,ad2.ca_street_name c_street_name
     ,ad2.ca_city c_city
     ,ad2.ca_zip c_zip
     ,d1.d_year as syear
     ,d2.d_year as fsyear
     ,d3.d_year s2year
     ,count(*) cnt
     ,sum(ss_wholesale_cost) s1
     ,sum(ss_list_price) s2
     ,sum(ss_coupon_amt) s3
  FROM   tpcds_2t_baseline.store_sales
        ,tpcds_2t_baseline.store_returns
        ,cs_ui
        ,tpcds_2t_baseline.date_dim d1
        ,tpcds_2t_baseline.date_dim d2
        ,tpcds_2t_baseline.date_dim d3
        ,tpcds_2t_baseline.store
        ,tpcds_2t_baseline.customer
        ,tpcds_2t_baseline.customer_demographics cd1
        ,tpcds_2t_baseline.customer_demographics cd2
        ,tpcds_2t_baseline.promotion
        ,tpcds_2t_baseline.household_demographics hd1
        ,tpcds_2t_baseline.household_demographics hd2
        ,tpcds_2t_baseline.customer_address ad1
        ,tpcds_2t_baseline.customer_address ad2
        ,tpcds_2t_baseline.income_band ib1
        ,tpcds_2t_baseline.income_band ib2
        ,tpcds_2t_baseline.item
  WHERE  ss_store_sk = s_store_sk AND
         ss_sold_date_sk = d1.d_date_sk AND
         ss_customer_sk = c_customer_sk AND
         ss_cdemo_sk= cd1.cd_demo_sk AND
         ss_hdemo_sk = hd1.hd_demo_sk AND
         ss_addr_sk = ad1.ca_address_sk and
         ss_item_sk = i_item_sk and
         ss_item_sk = sr_item_sk and
         ss_ticket_number = sr_ticket_number and
         ss_item_sk = cs_ui.cs_item_sk and
         c_current_cdemo_sk = cd2.cd_demo_sk AND
         c_current_hdemo_sk = hd2.hd_demo_sk AND
         c_current_addr_sk = ad2.ca_address_sk and
         c_first_sales_date_sk = d2.d_date_sk and
         c_first_shipto_date_sk = d3.d_date_sk and
         ss_promo_sk = p_promo_sk and
         hd1.hd_income_band_sk = ib1.ib_income_band_sk and
         hd2.hd_income_band_sk = ib2.ib_income_band_sk and
         cd1.cd_marital_status <> cd2.cd_marital_status and
         i_color in ('lawn','blush','smoke','ghost','floral','chartreuse') and
         i_current_price between 51 and 51 + 10 and
         i_current_price between 51 + 1 and 51 + 15
group by i_product_name
       ,i_item_sk
       ,s_store_name
       ,s_zip
       ,ad1.ca_street_number
       ,ad1.ca_street_name
       ,ad1.ca_city
       ,ad1.ca_zip
       ,ad2.ca_street_number
       ,ad2.ca_street_name
       ,ad2.ca_city
       ,ad2.ca_zip
       ,d1.d_year
       ,d2.d_year
       ,d3.d_year
)
select cs1.product_name
     ,cs1.store_name
     ,cs1.store_zip
     ,cs1.b_street_number
     ,cs1.b_street_name
     ,cs1.b_city
     ,cs1.b_zip
     ,cs1.c_street_number
     ,cs1.c_street_name
     ,cs1.c_city
     ,cs1.c_zip
     ,cs1.syear as syear1
     ,cs1.cnt as cnt1
     ,cs1.s1 as s11
     ,cs1.s2 as s21
     ,cs1.s3 as s31
     ,cs2.s1 as s12
     ,cs2.s2 as s22
     ,cs2.s3 as s32
     ,cs2.syear as syear2
     ,cs2.cnt as cnt2
from cross_sales cs1,cross_sales cs2
where cs1.item_sk=cs2.item_sk and
     cs1.syear = 2001 and
     cs2.syear = 2001 + 1 and
     cs2.cnt <= cs1.cnt and
     cs1.store_name = cs2.store_name and
     cs1.store_zip = cs2.store_zip
order by cs1.product_name
       ,cs1.store_name
       ,cs2.cnt
       ,cs1.s1
       ,cs2.s1;

-- end query 20 in stream 0 using template query64.tpl
-- start query 21 in stream 0 using template query36.tpl
select  
    sum(ss_net_profit)/sum(ss_ext_sales_price) as gross_margin
   ,i_category
   ,i_class
   ,concat(i_category, i_class) as lochierarchy
   ,rank() over (
 	partition by concat(i_category, i_class),
 	case when i_class = '0' then i_category end 
 	order by sum(ss_net_profit)/sum(ss_ext_sales_price) asc) as rank_within_parent
 from
    tpcds_2t_baseline.store_sales
   ,tpcds_2t_baseline.date_dim       d1
   ,tpcds_2t_baseline.item
   ,tpcds_2t_baseline.store
 where
    d1.d_year = 1999 
 and d1.d_date_sk = ss_sold_date_sk
 and i_item_sk  = ss_item_sk 
 and s_store_sk  = ss_store_sk
 and s_state in ('AL','TN','SD','SD',
                 'SD','SD','SD','SD')
 group by rollup(i_category,i_class)
 order by
   lochierarchy desc
  ,case when lochierarchy = '0' then i_category end
  ,rank_within_parent
  limit 100;

-- end query 21 in stream 0 using template query36.tpl
-- start query 22 in stream 0 using template query33.tpl
with ss as (
 select
          i_manufact_id,sum(ss_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.store_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_manufact_id in (select
  i_manufact_id
from
 tpcds_2t_baseline.item
where i_category in ('Electronics'))
 and     ss_item_sk              = i_item_sk
 and     ss_sold_date_sk         = d_date_sk
 and     d_year                  = 2002
 and     d_moy                   = 1
 and     ss_addr_sk              = ca_address_sk
 and     ca_gmt_offset           = -6 
 group by i_manufact_id),
 cs as (
 select
          i_manufact_id,sum(cs_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.catalog_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_manufact_id               in (select
  i_manufact_id
from
 tpcds_2t_baseline.item
where i_category in ('Electronics'))
 and     cs_item_sk              = i_item_sk
 and     cs_sold_date_sk         = d_date_sk
 and     d_year                  = 2002
 and     d_moy                   = 1
 and     cs_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -6 
 group by i_manufact_id),
 ws as (
 select
          i_manufact_id,sum(ws_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.web_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_manufact_id               in (select
  i_manufact_id
from
 tpcds_2t_baseline.item
where i_category in ('Electronics'))
 and     ws_item_sk              = i_item_sk
 and     ws_sold_date_sk         = d_date_sk
 and     d_year                  = 2002
 and     d_moy                   = 1
 and     ws_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -6
 group by i_manufact_id)
  select  i_manufact_id ,sum(total_sales) total_sales
 from  (select * from ss 
        union all
        select * from cs 
        union all
        select * from ws) tmp1
 group by i_manufact_id
 order by total_sales
limit 100;

-- end query 22 in stream 0 using template query33.tpl
-- start query 23 in stream 0 using template query46.tpl
select  c_last_name
       ,c_first_name
       ,ca_city
       ,bought_city
       ,ss_ticket_number
       ,amt,profit 
 from
   (select ss_ticket_number
          ,ss_customer_sk
          ,ca_city bought_city
          ,sum(ss_coupon_amt) amt
          ,sum(ss_net_profit) profit
    from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.store,tpcds_2t_baseline.household_demographics,tpcds_2t_baseline.customer_address 
    where store_sales.ss_sold_date_sk = date_dim.d_date_sk
    and store_sales.ss_store_sk = store.s_store_sk  
    and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
    and store_sales.ss_addr_sk = customer_address.ca_address_sk
    and (household_demographics.hd_dep_count = 3 or
         household_demographics.hd_vehicle_count= 4)
    and date_dim.d_dow in (6,0)
    and date_dim.d_year in (2000,2000+1,2000+2) 
    and store.s_city in ('Oak Grove','Fairview','Five Points','Riverside','Pleasant Hill') 
    group by ss_ticket_number,ss_customer_sk,ss_addr_sk,ca_city) dn,tpcds_2t_baseline.customer,tpcds_2t_baseline.customer_address current_addr
    where ss_customer_sk = c_customer_sk
      and customer.c_current_addr_sk = current_addr.ca_address_sk
      and current_addr.ca_city <> bought_city
  order by c_last_name
          ,c_first_name
          ,ca_city
          ,bought_city
          ,ss_ticket_number
  limit 100;

-- end query 23 in stream 0 using template query46.tpl
-- start query 24 in stream 0 using template query62.tpl
select  
   substr(w_warehouse_name,1,20) as warehouse_name
  ,sm_type
  ,web_name
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk <= 30 ) then 1 else 0 end)  as _30_days 
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 30) and 
                 (ws_ship_date_sk - ws_sold_date_sk <= 60) then 1 else 0 end )  as _31_to_60_days 
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 60) and 
                 (ws_ship_date_sk - ws_sold_date_sk <= 90) then 1 else 0 end)  as _61_to_90_days 
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk > 90) and
                 (ws_ship_date_sk - ws_sold_date_sk <= 120) then 1 else 0 end)  as _91_to_120_days 
  ,sum(case when (ws_ship_date_sk - ws_sold_date_sk  > 120) then 1 else 0 end)  as above_120_days 
from
   tpcds_2t_baseline.web_sales
  ,tpcds_2t_baseline.warehouse
  ,tpcds_2t_baseline.ship_mode
  ,tpcds_2t_baseline.web_site
  ,tpcds_2t_baseline.date_dim
where
    d_month_seq between 1211 and 1211 + 11
and ws_ship_date_sk   = d_date_sk
and ws_warehouse_sk   = w_warehouse_sk
and ws_ship_mode_sk   = sm_ship_mode_sk
and ws_web_site_sk    = web_site_sk
group by
   warehouse_name
  ,sm_type
  ,web_name
order by warehouse_name
        ,sm_type
       ,web_name
limit 100;

-- end query 24 in stream 0 using template query62.tpl
-- start query 25 in stream 0 using template query16.tpl
select  
   count(distinct cs_order_number) as order_count
  ,sum(cs_ext_ship_cost) as total_shipping_cost
  ,sum(cs_net_profit) as total_net_profit
from
   tpcds_2t_baseline.catalog_sales cs1
  ,tpcds_2t_baseline.date_dim
  ,tpcds_2t_baseline.customer_address
  ,tpcds_2t_baseline.call_center
where
    d_date between '1999-4-01' and 
           date_add(date '1999-4-01', interval 60 day)
and cs1.cs_ship_date_sk = d_date_sk
and cs1.cs_ship_addr_sk = ca_address_sk
and ca_state = 'MD'
and cs1.cs_call_center_sk = cc_call_center_sk
and cc_county in ('Ziebach County','Williamson County','Walker County','Ziebach County',
                  'Ziebach County'
)
and exists (select *
            from tpcds_2t_baseline.catalog_sales cs2
            where cs1.cs_order_number = cs2.cs_order_number
              and cs1.cs_warehouse_sk <> cs2.cs_warehouse_sk)
and not exists(select *
               from tpcds_2t_baseline.catalog_returns cr1
               where cs1.cs_order_number = cr1.cr_order_number)
order by count(distinct cs_order_number)
limit 100;

-- end query 25 in stream 0 using template query16.tpl
-- start query 26 in stream 0 using template query10.tpl
select  
  cd_gender,
  cd_marital_status,
  cd_education_status,
  count(*) cnt1,
  cd_purchase_estimate,
  count(*) cnt2,
  cd_credit_rating,
  count(*) cnt3,
  cd_dep_count,
  count(*) cnt4,
  cd_dep_employed_count,
  count(*) cnt5,
  cd_dep_college_count,
  count(*) cnt6
 from
  tpcds_2t_baseline.customer c,tpcds_2t_baseline.customer_address ca,tpcds_2t_baseline.customer_demographics
 where
  c.c_current_addr_sk = ca.ca_address_sk and
  ca_county in ('Bottineau County','Marion County','Randolph County','Providence County','Sagadahoc County') and
  cd_demo_sk = c.c_current_cdemo_sk and 
  exists (select *
          from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
          where c.c_customer_sk = ss_customer_sk and
                ss_sold_date_sk = d_date_sk and
                d_year = 2000 and
                d_moy between 1 and 1+3) and
   (exists (select *
            from tpcds_2t_baseline.web_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = ws_bill_customer_sk and
                  ws_sold_date_sk = d_date_sk and
                  d_year = 2000 and
                  d_moy between 1 ANd 1+3) or 
    exists (select * 
            from tpcds_2t_baseline.catalog_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = cs_ship_customer_sk and
                  cs_sold_date_sk = d_date_sk and
                  d_year = 2000 and
                  d_moy between 1 and 1+3))
 group by cd_gender,
          cd_marital_status,
          cd_education_status,
          cd_purchase_estimate,
          cd_credit_rating,
          cd_dep_count,
          cd_dep_employed_count,
          cd_dep_college_count
 order by cd_gender,
          cd_marital_status,
          cd_education_status,
          cd_purchase_estimate,
          cd_credit_rating,
          cd_dep_count,
          cd_dep_employed_count,
          cd_dep_college_count
limit 100;

-- end query 26 in stream 0 using template query10.tpl
-- start query 27 in stream 0 using template query63.tpl
select  * 
from (select i_manager_id
             ,sum(ss_sales_price) sum_sales
             ,avg(sum(ss_sales_price)) over (partition by i_manager_id) avg_monthly_sales
      from tpcds_2t_baseline.item
          ,tpcds_2t_baseline.store_sales
          ,tpcds_2t_baseline.date_dim
          ,tpcds_2t_baseline.store
      where ss_item_sk = i_item_sk
        and ss_sold_date_sk = d_date_sk
        and ss_store_sk = s_store_sk
        and d_month_seq in (1179,1179+1,1179+2,1179+3,1179+4,1179+5,1179+6,1179+7,1179+8,1179+9,1179+10,1179+11)
        and ((    i_category in ('Books','Children','Electronics')
              and i_class in ('personal','portable','reference','self-help')
              and i_brand in ('scholaramalgamalg #14','scholaramalgamalg #7',
		                  'exportiunivamalg #9','scholaramalgamalg #9'))
           or(    i_category in ('Women','Music','Men')
              and i_class in ('accessories','classical','fragrances','pants')
              and i_brand in ('amalgimporto #1','edu packscholar #1','exportiimporto #1',
		                 'importoamalg #1')))
group by i_manager_id, d_moy) tmp1
where case when avg_monthly_sales > 0 then abs (sum_sales - avg_monthly_sales) / avg_monthly_sales else null end > 0.1
order by i_manager_id
        ,avg_monthly_sales
        ,sum_sales
limit 100;

-- end query 27 in stream 0 using template query63.tpl
-- start query 28 in stream 0 using template query69.tpl
select  
  cd_gender,
  cd_marital_status,
  cd_education_status,
  count(*) cnt1,
  cd_purchase_estimate,
  count(*) cnt2,
  cd_credit_rating,
  count(*) cnt3
 from
  tpcds_2t_baseline.customer c,tpcds_2t_baseline.customer_address ca,tpcds_2t_baseline.customer_demographics
 where
  c.c_current_addr_sk = ca.ca_address_sk and
  ca_state in ('IN','ND','PA') and
  cd_demo_sk = c.c_current_cdemo_sk and 
  exists (select *
          from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
          where c.c_customer_sk = ss_customer_sk and
                ss_sold_date_sk = d_date_sk and
                d_year = 1999 and
                d_moy between 2 and 2+2) and
   (not exists (select *
            from tpcds_2t_baseline.web_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = ws_bill_customer_sk and
                  ws_sold_date_sk = d_date_sk and
                  d_year = 1999 and
                  d_moy between 2 and 2+2) and
    not exists (select * 
            from tpcds_2t_baseline.catalog_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = cs_ship_customer_sk and
                  cs_sold_date_sk = d_date_sk and
                  d_year = 1999 and
                  d_moy between 2 and 2+2))
 group by cd_gender,
          cd_marital_status,
          cd_education_status,
          cd_purchase_estimate,
          cd_credit_rating
 order by cd_gender,
          cd_marital_status,
          cd_education_status,
          cd_purchase_estimate,
          cd_credit_rating
 limit 100;

-- end query 28 in stream 0 using template query69.tpl
-- start query 29 in stream 0 using template query60.tpl
with ss as (
 select
          i_item_id,sum(ss_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.store_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_item_id in (select
  i_item_id
from
 tpcds_2t_baseline.item
where i_category in ('Music'))
 and     ss_item_sk              = i_item_sk
 and     ss_sold_date_sk         = d_date_sk
 and     d_year                  = 1998
 and     d_moy                   = 10
 and     ss_addr_sk              = ca_address_sk
 and     ca_gmt_offset           = -5 
 group by i_item_id),
 cs as (
 select
          i_item_id,sum(cs_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.catalog_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_item_id               in (select
  i_item_id
from
 tpcds_2t_baseline.item
where i_category in ('Music'))
 and     cs_item_sk              = i_item_sk
 and     cs_sold_date_sk         = d_date_sk
 and     d_year                  = 1998
 and     d_moy                   = 10
 and     cs_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -5 
 group by i_item_id),
 ws as (
 select
          i_item_id,sum(ws_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.web_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_item_id               in (select
  i_item_id
from
 tpcds_2t_baseline.item
where i_category in ('Music'))
 and     ws_item_sk              = i_item_sk
 and     ws_sold_date_sk         = d_date_sk
 and     d_year                  = 1998
 and     d_moy                   = 10
 and     ws_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -5
 group by i_item_id)
  select   
  i_item_id
,sum(total_sales) total_sales
 from  (select * from ss 
        union all
        select * from cs 
        union all
        select * from ws) tmp1
 group by i_item_id
 order by i_item_id
      ,total_sales
 limit 100;

-- end query 29 in stream 0 using template query60.tpl
-- start query 30 in stream 0 using template query59.tpl
with wss as 
 (select d_week_seq,
        ss_store_sk,
        sum(case when (d_day_name='Sunday') then ss_sales_price else null end) sun_sales,
        sum(case when (d_day_name='Monday') then ss_sales_price else null end) mon_sales,
        sum(case when (d_day_name='Tuesday') then ss_sales_price else  null end) tue_sales,
        sum(case when (d_day_name='Wednesday') then ss_sales_price else null end) wed_sales,
        sum(case when (d_day_name='Thursday') then ss_sales_price else null end) thu_sales,
        sum(case when (d_day_name='Friday') then ss_sales_price else null end) fri_sales,
        sum(case when (d_day_name='Saturday') then ss_sales_price else null end) sat_sales
 from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
 where d_date_sk = ss_sold_date_sk
 group by d_week_seq,ss_store_sk
 )
  select  s_store_name1,s_store_id1,d_week_seq1
       ,sun_sales1/sun_sales2,mon_sales1/mon_sales2
       ,tue_sales1/tue_sales2,wed_sales1/wed_sales2,thu_sales1/thu_sales2
       ,fri_sales1/fri_sales2,sat_sales1/sat_sales2
 from
 (select s_store_name s_store_name1,wss.d_week_seq d_week_seq1
        ,s_store_id s_store_id1,sun_sales sun_sales1
        ,mon_sales mon_sales1,tue_sales tue_sales1
        ,wed_sales wed_sales1,thu_sales thu_sales1
        ,fri_sales fri_sales1,sat_sales sat_sales1
  from wss,tpcds_2t_baseline.store,tpcds_2t_baseline.date_dim d
  where d.d_week_seq = wss.d_week_seq and
        ss_store_sk = s_store_sk and 
        d_month_seq between 1202 and 1202 + 11) y,
 (select s_store_name s_store_name2,wss.d_week_seq d_week_seq2
        ,s_store_id s_store_id2,sun_sales sun_sales2
        ,mon_sales mon_sales2,tue_sales tue_sales2
        ,wed_sales wed_sales2,thu_sales thu_sales2
        ,fri_sales fri_sales2,sat_sales sat_sales2
  from wss,tpcds_2t_baseline.store,tpcds_2t_baseline.date_dim d
  where d.d_week_seq = wss.d_week_seq and
        ss_store_sk = s_store_sk and 
        d_month_seq between 1202+ 12 and 1202 + 23) x
 where s_store_id1=s_store_id2
   and d_week_seq1=d_week_seq2-52
 order by s_store_name1,s_store_id1,d_week_seq1
limit 100;

-- end query 30 in stream 0 using template query59.tpl
-- start query 31 in stream 0 using template query37.tpl
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from tpcds_2t_baseline.item, tpcds_2t_baseline.inventory, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.catalog_sales
 where i_current_price between 16 and 16 + 30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between date(1999, 03, 27) and date_add(date '1999-03-27', interval 60 day)
 and i_manufact_id in (821,673,849,745)
 and inv_quantity_on_hand between 100 and 500
 and cs_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;

-- end query 31 in stream 0 using template query37.tpl
-- start query 32 in stream 0 using template query98.tpl
select i_item_id
      ,i_item_desc 
      ,i_category 
      ,i_class 
      ,i_current_price
      ,sum(ss_ext_sales_price) as itemrevenue 
      ,sum(ss_ext_sales_price)*100/sum(sum(ss_ext_sales_price)) over
          (partition by i_class) as revenueratio
from	
	tpcds_2t_baseline.store_sales
    	,tpcds_2t_baseline.item 
    	,tpcds_2t_baseline.date_dim
where 
	ss_item_sk = i_item_sk 
  	and i_category in ('Children', 'Women', 'Shoes')
  	and ss_sold_date_sk = d_date_sk
	and d_date between date(2001, 03, 09) 
				and date_add(date '2001-03-09', interval 30 day)
group by 
	i_item_id
        ,i_item_desc 
        ,i_category
        ,i_class
        ,i_current_price
order by 
	i_category
        ,i_class
        ,i_item_id
        ,i_item_desc
        ,revenueratio;

-- end query 32 in stream 0 using template query98.tpl
-- start query 33 in stream 0 using template query85.tpl
select  substr(r_reason_desc,1,20)
       ,avg(ws_quantity)
       ,avg(wr_refunded_cash)
       ,avg(wr_fee)
 from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.web_returns, tpcds_2t_baseline.web_page, tpcds_2t_baseline.customer_demographics cd1,
      tpcds_2t_baseline.customer_demographics cd2, tpcds_2t_baseline.customer_address, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.reason 
 where ws_web_page_sk = wp_web_page_sk
   and ws_item_sk = wr_item_sk
   and ws_order_number = wr_order_number
   and ws_sold_date_sk = d_date_sk and d_year = 2001
   and cd1.cd_demo_sk = wr_refunded_cdemo_sk 
   and cd2.cd_demo_sk = wr_returning_cdemo_sk
   and ca_address_sk = wr_refunded_addr_sk
   and r_reason_sk = wr_reason_sk
   and
   (
    (
     cd1.cd_marital_status = 'W'
     and
     cd1.cd_marital_status = cd2.cd_marital_status
     and
     cd1.cd_education_status = 'Primary'
     and 
     cd1.cd_education_status = cd2.cd_education_status
     and
     ws_sales_price between 100.00 and 150.00
    )
   or
    (
     cd1.cd_marital_status = 'D'
     and
     cd1.cd_marital_status = cd2.cd_marital_status
     and
     cd1.cd_education_status = 'College' 
     and
     cd1.cd_education_status = cd2.cd_education_status
     and
     ws_sales_price between 50.00 and 100.00
    )
   or
    (
     cd1.cd_marital_status = 'S'
     and
     cd1.cd_marital_status = cd2.cd_marital_status
     and
     cd1.cd_education_status = '2 yr Degree'
     and
     cd1.cd_education_status = cd2.cd_education_status
     and
     ws_sales_price between 150.00 and 200.00
    )
   )
   and
   (
    (
     ca_country = 'United States'
     and
     ca_state in ('PA', 'IN', 'VA')
     and ws_net_profit between 100 and 200  
    )
    or
    (
     ca_country = 'United States'
     and
     ca_state in ('TX', 'MO', 'MS')
     and ws_net_profit between 150 and 300  
    )
    or
    (
     ca_country = 'United States'
     and
     ca_state in ('MT', 'OR', 'MN')
     and ws_net_profit between 50 and 250  
    )
   )
group by r_reason_desc
order by substr(r_reason_desc,1,20)
        ,avg(ws_quantity)
        ,avg(wr_refunded_cash)
        ,avg(wr_fee)
limit 100;

-- end query 33 in stream 0 using template query85.tpl
-- start query 34 in stream 0 using template query70.tpl
select  
    sum(ss_net_profit) as total_sum
   ,s_state
   ,s_county
   ,concat(s_state, s_county) as lochierarchy
   ,rank() over (
 	partition by concat(s_state, s_county),
 	case when s_county = '0' then s_state end 
 	order by sum(ss_net_profit) desc) as rank_within_parent
 from
    tpcds_2t_baseline.store_sales
   ,tpcds_2t_baseline.date_dim       d1
   ,tpcds_2t_baseline.store
 where
    d1.d_month_seq between 1191 and 1191+11
 and d1.d_date_sk = ss_sold_date_sk
 and s_store_sk  = ss_store_sk
 and s_state in
             ( select s_state
               from  (select s_state as s_state,
 			    rank() over ( partition by s_state order by sum(ss_net_profit) desc) as ranking
                      from   tpcds_2t_baseline.store_sales, tpcds_2t_baseline.store, tpcds_2t_baseline.date_dim
                      where  d_month_seq between 1191 and 1191+11
 			    and d_date_sk = ss_sold_date_sk
 			    and s_store_sk  = ss_store_sk
                      group by s_state
                     ) tmp1 
               where ranking <= 5
             )
 group by rollup(s_state,s_county)
 order by
   lochierarchy desc
  ,case when lochierarchy = '0' then s_state end
  ,rank_within_parent
 limit 100;

-- end query 34 in stream 0 using template query70.tpl
-- start query 35 in stream 0 using template query67.tpl
select  *
from (select i_category
            ,i_class
            ,i_brand
            ,i_product_name
            ,d_year
            ,d_qoy
            ,d_moy
            ,s_store_id
            ,sumsales
            ,rank() over (partition by i_category order by sumsales desc) rk
      from (select i_category
                  ,i_class
                  ,i_brand
                  ,i_product_name
                  ,d_year
                  ,d_qoy
                  ,d_moy
                  ,s_store_id
                  ,sum(coalesce(ss_sales_price*ss_quantity,0)) sumsales
            from tpcds_2t_baseline.store_sales
                ,tpcds_2t_baseline.date_dim
                ,tpcds_2t_baseline.store
                ,tpcds_2t_baseline.item
       where  ss_sold_date_sk=d_date_sk
          and ss_item_sk=i_item_sk
          and ss_store_sk = s_store_sk
          and d_month_seq between 1192 and 1192+11
       group by  rollup(i_category, i_class, i_brand, i_product_name, d_year, d_qoy, d_moy,s_store_id))dw1) dw2
where rk <= 100
order by i_category
        ,i_class
        ,i_brand
        ,i_product_name
        ,d_year
        ,d_qoy
        ,d_moy
        ,s_store_id
        ,sumsales
        ,rk
limit 100;

-- end query 35 in stream 0 using template query67.tpl
-- start query 36 in stream 0 using template query28.tpl
select  *
from (select avg(ss_list_price) B1_LP
            ,count(ss_list_price) B1_CNT
            ,count(distinct ss_list_price) B1_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 0 and 5
        and (ss_list_price between 49 and 49+10 
             or ss_coupon_amt between 5040 and 5040+1000
             or ss_wholesale_cost between 4 and 4+20)) B1,
     (select avg(ss_list_price) B2_LP
            ,count(ss_list_price) B2_CNT
            ,count(distinct ss_list_price) B2_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 6 and 10
        and (ss_list_price between 5 and 5+10
          or ss_coupon_amt between 441 and 441+1000
          or ss_wholesale_cost between 80 and 80+20)) B2,
     (select avg(ss_list_price) B3_LP
            ,count(ss_list_price) B3_CNT
            ,count(distinct ss_list_price) B3_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 11 and 15
        and (ss_list_price between 153 and 153+10
          or ss_coupon_amt between 10459 and 10459+1000
          or ss_wholesale_cost between 3 and 3+20)) B3,
     (select avg(ss_list_price) B4_LP
            ,count(ss_list_price) B4_CNT
            ,count(distinct ss_list_price) B4_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 16 and 20
        and (ss_list_price between 14 and 14+10
          or ss_coupon_amt between 13311 and 13311+1000
          or ss_wholesale_cost between 1 and 1+20)) B4,
     (select avg(ss_list_price) B5_LP
            ,count(ss_list_price) B5_CNT
            ,count(distinct ss_list_price) B5_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 21 and 25
        and (ss_list_price between 29 and 29+10
          or ss_coupon_amt between 6047 and 6047+1000
          or ss_wholesale_cost between 27 and 27+20)) B5,
     (select avg(ss_list_price) B6_LP
            ,count(ss_list_price) B6_CNT
            ,count(distinct ss_list_price) B6_CNTD
      from tpcds_2t_baseline.store_sales
      where ss_quantity between 26 and 30
        and (ss_list_price between 159 and 159+10
          or ss_coupon_amt between 2432 and 2432+1000
          or ss_wholesale_cost between 48 and 48+20)) B6
limit 100;

-- end query 36 in stream 0 using template query28.tpl
-- start query 37 in stream 0 using template query81.tpl
with customer_total_return as
 (select cr_returning_customer_sk as ctr_customer_sk
        ,ca_state as ctr_state, 
 	sum(cr_return_amt_inc_tax) as ctr_total_return
 from tpcds_2t_baseline.catalog_returns
     ,tpcds_2t_baseline.date_dim
     ,tpcds_2t_baseline.customer_address
 where cr_returned_date_sk = d_date_sk 
   and d_year =2002
   and cr_returning_addr_sk = ca_address_sk 
 group by cr_returning_customer_sk
         ,ca_state )
  select  c_customer_id,c_salutation,c_first_name,c_last_name,ca_street_number,ca_street_name
                   ,ca_street_type,ca_suite_number,ca_city,ca_county,ca_state,ca_zip,ca_country,ca_gmt_offset
                  ,ca_location_type,ctr_total_return
 from customer_total_return ctr1
     ,tpcds_2t_baseline.customer_address
     ,tpcds_2t_baseline.customer
 where ctr1.ctr_total_return > (select avg(ctr_total_return)*1.2
 			  from customer_total_return ctr2 
                  	  where ctr1.ctr_state = ctr2.ctr_state)
       and ca_address_sk = c_current_addr_sk
       and ca_state = 'IL'
       and ctr1.ctr_customer_sk = c_customer_sk
 order by c_customer_id,c_salutation,c_first_name,c_last_name,ca_street_number,ca_street_name
                   ,ca_street_type,ca_suite_number,ca_city,ca_county,ca_state,ca_zip,ca_country,ca_gmt_offset
                  ,ca_location_type,ctr_total_return
 limit 100;

-- end query 37 in stream 0 using template query81.tpl
-- start query 38 in stream 0 using template query97.tpl
with ssci as (
select ss_customer_sk customer_sk
      ,ss_item_sk item_sk
from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
where ss_sold_date_sk = d_date_sk
  and d_month_seq between 1176 and 1176 + 11
group by ss_customer_sk
        ,ss_item_sk),
csci as(
 select cs_bill_customer_sk customer_sk
      ,cs_item_sk item_sk
from tpcds_2t_baseline.catalog_sales,tpcds_2t_baseline.date_dim
where cs_sold_date_sk = d_date_sk
  and d_month_seq between 1176 and 1176 + 11
group by cs_bill_customer_sk
        ,cs_item_sk)
 select  sum(case when ssci.customer_sk is not null and csci.customer_sk is null then 1 else 0 end) store_only
      ,sum(case when ssci.customer_sk is null and csci.customer_sk is not null then 1 else 0 end) catalog_only
      ,sum(case when ssci.customer_sk is not null and csci.customer_sk is not null then 1 else 0 end) store_and_catalog
from ssci full outer join csci on (ssci.customer_sk=csci.customer_sk
                               and ssci.item_sk = csci.item_sk)
limit 100;

-- end query 38 in stream 0 using template query97.tpl
-- start query 39 in stream 0 using template query66.tpl
select   
         w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
        ,ship_carriers
        ,year
 	,sum(jan_sales) as jan_sales
 	,sum(feb_sales) as feb_sales
 	,sum(mar_sales) as mar_sales
 	,sum(apr_sales) as apr_sales
 	,sum(may_sales) as may_sales
 	,sum(jun_sales) as jun_sales
 	,sum(jul_sales) as jul_sales
 	,sum(aug_sales) as aug_sales
 	,sum(sep_sales) as sep_sales
 	,sum(oct_sales) as oct_sales
 	,sum(nov_sales) as nov_sales
 	,sum(dec_sales) as dec_sales
 	,sum(jan_sales/w_warehouse_sq_ft) as jan_sales_per_sq_foot
 	,sum(feb_sales/w_warehouse_sq_ft) as feb_sales_per_sq_foot
 	,sum(mar_sales/w_warehouse_sq_ft) as mar_sales_per_sq_foot
 	,sum(apr_sales/w_warehouse_sq_ft) as apr_sales_per_sq_foot
 	,sum(may_sales/w_warehouse_sq_ft) as may_sales_per_sq_foot
 	,sum(jun_sales/w_warehouse_sq_ft) as jun_sales_per_sq_foot
 	,sum(jul_sales/w_warehouse_sq_ft) as jul_sales_per_sq_foot
 	,sum(aug_sales/w_warehouse_sq_ft) as aug_sales_per_sq_foot
 	,sum(sep_sales/w_warehouse_sq_ft) as sep_sales_per_sq_foot
 	,sum(oct_sales/w_warehouse_sq_ft) as oct_sales_per_sq_foot
 	,sum(nov_sales/w_warehouse_sq_ft) as nov_sales_per_sq_foot
 	,sum(dec_sales/w_warehouse_sq_ft) as dec_sales_per_sq_foot
 	,sum(jan_net) as jan_net
 	,sum(feb_net) as feb_net
 	,sum(mar_net) as mar_net
 	,sum(apr_net) as apr_net
 	,sum(may_net) as may_net
 	,sum(jun_net) as jun_net
 	,sum(jul_net) as jul_net
 	,sum(aug_net) as aug_net
 	,sum(sep_net) as sep_net
 	,sum(oct_net) as oct_net
 	,sum(nov_net) as nov_net
 	,sum(dec_net) as dec_net
 from (
     select 
 	w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
 	, concat('ZOUROS', ',', 'ZHOU') as ship_carriers
       ,d_year as year
 	,sum(case when d_moy = 1 
 		then ws_sales_price* ws_quantity else 0 end) as jan_sales
 	,sum(case when d_moy = 2 
 		then ws_sales_price* ws_quantity else 0 end) as feb_sales
 	,sum(case when d_moy = 3 
 		then ws_sales_price* ws_quantity else 0 end) as mar_sales
 	,sum(case when d_moy = 4 
 		then ws_sales_price* ws_quantity else 0 end) as apr_sales
 	,sum(case when d_moy = 5 
 		then ws_sales_price* ws_quantity else 0 end) as may_sales
 	,sum(case when d_moy = 6 
 		then ws_sales_price* ws_quantity else 0 end) as jun_sales
 	,sum(case when d_moy = 7 
 		then ws_sales_price* ws_quantity else 0 end) as jul_sales
 	,sum(case when d_moy = 8 
 		then ws_sales_price* ws_quantity else 0 end) as aug_sales
 	,sum(case when d_moy = 9 
 		then ws_sales_price* ws_quantity else 0 end) as sep_sales
 	,sum(case when d_moy = 10 
 		then ws_sales_price* ws_quantity else 0 end) as oct_sales
 	,sum(case when d_moy = 11
 		then ws_sales_price* ws_quantity else 0 end) as nov_sales
 	,sum(case when d_moy = 12
 		then ws_sales_price* ws_quantity else 0 end) as dec_sales
 	,sum(case when d_moy = 1 
 		then ws_net_paid * ws_quantity else 0 end) as jan_net
 	,sum(case when d_moy = 2
 		then ws_net_paid * ws_quantity else 0 end) as feb_net
 	,sum(case when d_moy = 3 
 		then ws_net_paid * ws_quantity else 0 end) as mar_net
 	,sum(case when d_moy = 4 
 		then ws_net_paid * ws_quantity else 0 end) as apr_net
 	,sum(case when d_moy = 5 
 		then ws_net_paid * ws_quantity else 0 end) as may_net
 	,sum(case when d_moy = 6 
 		then ws_net_paid * ws_quantity else 0 end) as jun_net
 	,sum(case when d_moy = 7 
 		then ws_net_paid * ws_quantity else 0 end) as jul_net
 	,sum(case when d_moy = 8 
 		then ws_net_paid * ws_quantity else 0 end) as aug_net
 	,sum(case when d_moy = 9 
 		then ws_net_paid * ws_quantity else 0 end) as sep_net
 	,sum(case when d_moy = 10 
 		then ws_net_paid * ws_quantity else 0 end) as oct_net
 	,sum(case when d_moy = 11
 		then ws_net_paid * ws_quantity else 0 end) as nov_net
 	,sum(case when d_moy = 12
 		then ws_net_paid * ws_quantity else 0 end) as dec_net
     from
          tpcds_2t_baseline.web_sales
         ,tpcds_2t_baseline.warehouse
         ,tpcds_2t_baseline.date_dim
         ,tpcds_2t_baseline.time_dim
 	  ,tpcds_2t_baseline.ship_mode
     where
            ws_warehouse_sk =  w_warehouse_sk
        and ws_sold_date_sk = d_date_sk
        and ws_sold_time_sk = t_time_sk
 	and ws_ship_mode_sk = sm_ship_mode_sk
        and d_year = 2000
 	and t_time between 18479 and 18479+28800 
 	and sm_carrier in ('ZOUROS','ZHOU')
     group by 
        w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
       ,d_year
 union all
     select 
 	w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
 	, concat('ZOUROS', ',', 'ZHOU') as ship_carriers
       ,d_year as year
 	,sum(case when d_moy = 1 
 		then cs_ext_sales_price* cs_quantity else 0 end) as jan_sales
 	,sum(case when d_moy = 2 
 		then cs_ext_sales_price* cs_quantity else 0 end) as feb_sales
 	,sum(case when d_moy = 3 
 		then cs_ext_sales_price* cs_quantity else 0 end) as mar_sales
 	,sum(case when d_moy = 4 
 		then cs_ext_sales_price* cs_quantity else 0 end) as apr_sales
 	,sum(case when d_moy = 5 
 		then cs_ext_sales_price* cs_quantity else 0 end) as may_sales
 	,sum(case when d_moy = 6 
 		then cs_ext_sales_price* cs_quantity else 0 end) as jun_sales
 	,sum(case when d_moy = 7 
 		then cs_ext_sales_price* cs_quantity else 0 end) as jul_sales
 	,sum(case when d_moy = 8 
 		then cs_ext_sales_price* cs_quantity else 0 end) as aug_sales
 	,sum(case when d_moy = 9 
 		then cs_ext_sales_price* cs_quantity else 0 end) as sep_sales
 	,sum(case when d_moy = 10 
 		then cs_ext_sales_price* cs_quantity else 0 end) as oct_sales
 	,sum(case when d_moy = 11
 		then cs_ext_sales_price* cs_quantity else 0 end) as nov_sales
 	,sum(case when d_moy = 12
 		then cs_ext_sales_price* cs_quantity else 0 end) as dec_sales
 	,sum(case when d_moy = 1 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as jan_net
 	,sum(case when d_moy = 2 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as feb_net
 	,sum(case when d_moy = 3 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as mar_net
 	,sum(case when d_moy = 4 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as apr_net
 	,sum(case when d_moy = 5 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as may_net
 	,sum(case when d_moy = 6 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as jun_net
 	,sum(case when d_moy = 7 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as jul_net
 	,sum(case when d_moy = 8 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as aug_net
 	,sum(case when d_moy = 9 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as sep_net
 	,sum(case when d_moy = 10 
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as oct_net
 	,sum(case when d_moy = 11
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as nov_net
 	,sum(case when d_moy = 12
 		then cs_net_paid_inc_ship * cs_quantity else 0 end) as dec_net
     from
          tpcds_2t_baseline.catalog_sales
         ,tpcds_2t_baseline.warehouse
         ,tpcds_2t_baseline.date_dim
         ,tpcds_2t_baseline.time_dim
 	 ,tpcds_2t_baseline.ship_mode
     where
            cs_warehouse_sk =  w_warehouse_sk
        and cs_sold_date_sk = d_date_sk
        and cs_sold_time_sk = t_time_sk
 	and cs_ship_mode_sk = sm_ship_mode_sk
        and d_year = 2000
 	and t_time between 18479 AND 18479+28800 
 	and sm_carrier in ('ZOUROS','ZHOU')
     group by 
        w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
       ,d_year
 ) x
 group by 
        w_warehouse_name
 	,w_warehouse_sq_ft
 	,w_city
 	,w_county
 	,w_state
 	,w_country
 	,ship_carriers
       ,year
 order by w_warehouse_name
 limit 100;

-- end query 39 in stream 0 using template query66.tpl
-- start query 40 in stream 0 using template query90.tpl
select  cast(amc as numeric) / cast(pmc as numeric) am_pm_ratio
 from ( select count(*) amc
       from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.web_page
       where ws_sold_time_sk = time_dim.t_time_sk
         and ws_ship_hdemo_sk = household_demographics.hd_demo_sk
         and ws_web_page_sk = web_page.wp_web_page_sk
         and time_dim.t_hour between 12 and 12+1
         and household_demographics.hd_dep_count = 0
         and web_page.wp_char_count between 5000 and 5200),
      ( select count(*) pmc
       from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.web_page
       where ws_sold_time_sk = time_dim.t_time_sk
         and ws_ship_hdemo_sk = household_demographics.hd_demo_sk
         and ws_web_page_sk = web_page.wp_web_page_sk
         and time_dim.t_hour between 15 and 15+1
         and household_demographics.hd_dep_count = 0
         and web_page.wp_char_count between 5000 and 5200)
 order by am_pm_ratio
 limit 100;

-- end query 40 in stream 0 using template query90.tpl
-- start query 41 in stream 0 using template query17.tpl
select  i_item_id
       ,i_item_desc
       ,s_state
       ,count(ss_quantity) as store_sales_quantitycount
       ,avg(ss_quantity) as store_sales_quantityave
       ,stddev_samp(ss_quantity) as store_sales_quantitystdev
       ,stddev_samp(ss_quantity)/avg(ss_quantity) as store_sales_quantitycov
       ,count(sr_return_quantity) as store_returns_quantitycount
       ,avg(sr_return_quantity) as store_returns_quantityave
       ,stddev_samp(sr_return_quantity) as store_returns_quantitystdev
       ,stddev_samp(sr_return_quantity)/avg(sr_return_quantity) as store_returns_quantitycov
       ,count(cs_quantity) as catalog_sales_quantitycount ,avg(cs_quantity) as catalog_sales_quantityave
       ,stddev_samp(cs_quantity) as catalog_sales_quantitystdev
       ,stddev_samp(cs_quantity)/avg(cs_quantity) as catalog_sales_quantitycov
 from tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.store_returns
     ,tpcds_2t_baseline.catalog_sales
     ,tpcds_2t_baseline.date_dim d1
     ,tpcds_2t_baseline.date_dim d2
     ,tpcds_2t_baseline.date_dim d3
     ,tpcds_2t_baseline.store
     ,tpcds_2t_baseline.item
 where d1.d_quarter_name = '2001Q1'
   and d1.d_date_sk = ss_sold_date_sk
   and i_item_sk = ss_item_sk
   and s_store_sk = ss_store_sk
   and ss_customer_sk = sr_customer_sk
   and ss_item_sk = sr_item_sk
   and ss_ticket_number = sr_ticket_number
   and sr_returned_date_sk = d2.d_date_sk
   and d2.d_quarter_name in ('2001Q1','2001Q2','2001Q3')
   and sr_customer_sk = cs_bill_customer_sk
   and sr_item_sk = cs_item_sk
   and cs_sold_date_sk = d3.d_date_sk
   and d3.d_quarter_name in ('2001Q1','2001Q2','2001Q3')
 group by i_item_id
         ,i_item_desc
         ,s_state
 order by i_item_id
         ,i_item_desc
         ,s_state
limit 100;

-- end query 41 in stream 0 using template query17.tpl
-- start query 42 in stream 0 using template query47.tpl
with v1 as(
 select i_category, i_brand,
        s_store_name, s_company_name,
        d_year, d_moy,
        sum(ss_sales_price) sum_sales,
        avg(sum(ss_sales_price)) over
          (partition by i_category, i_brand,
                     s_store_name, s_company_name, d_year)
          avg_monthly_sales,
        rank() over
          (partition by i_category, i_brand,
                     s_store_name, s_company_name
           order by d_year, d_moy) rn
 from tpcds_2t_baseline.item, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store
 where ss_item_sk = i_item_sk and
       ss_sold_date_sk = d_date_sk and
       ss_store_sk = s_store_sk and
       (
         d_year = 2001 or
         ( d_year = 2001-1 and d_moy =12) or
         ( d_year = 2001+1 and d_moy =1)
       )
 group by i_category, i_brand,
          s_store_name, s_company_name,
          d_year, d_moy),
 v2 as(
 select v1.s_company_name
        ,v1.d_year, v1.d_moy
        ,v1.avg_monthly_sales
        ,v1.sum_sales, v1_lag.sum_sales psum, v1_lead.sum_sales nsum
 from v1, v1 v1_lag, v1 v1_lead
 where v1.i_category = v1_lag.i_category and
       v1.i_category = v1_lead.i_category and
       v1.i_brand = v1_lag.i_brand and
       v1.i_brand = v1_lead.i_brand and
       v1.s_store_name = v1_lag.s_store_name and
       v1.s_store_name = v1_lead.s_store_name and
       v1.s_company_name = v1_lag.s_company_name and
       v1.s_company_name = v1_lead.s_company_name and
       v1.rn = v1_lag.rn + 1 and
       v1.rn = v1_lead.rn - 1)
  select  *
 from v2
 where  d_year = 2001 and    
        avg_monthly_sales > 0 and
        case when avg_monthly_sales > 0 then abs(sum_sales - avg_monthly_sales) / avg_monthly_sales else null end > 0.1
 order by sum_sales - avg_monthly_sales, avg_monthly_sales
 limit 100;

-- end query 42 in stream 0 using template query47.tpl
-- start query 43 in stream 0 using template query95.tpl
with ws_wh as
(select ws1.ws_order_number,ws1.ws_warehouse_sk wh1,ws2.ws_warehouse_sk wh2
 from tpcds_2t_baseline.web_sales ws1,tpcds_2t_baseline.web_sales ws2
 where ws1.ws_order_number = ws2.ws_order_number
   and ws1.ws_warehouse_sk <> ws2.ws_warehouse_sk)
 select  
   count(distinct ws_order_number) as order_count
  ,sum(ws_ext_ship_cost) as total_shipping_cost
  ,sum(ws_net_profit) as total_net_profit
from
   tpcds_2t_baseline.web_sales ws1
  ,tpcds_2t_baseline.date_dim
  ,tpcds_2t_baseline.customer_address
  ,tpcds_2t_baseline.web_site
where
    d_date between date(1999, 03, 01) and 
           date_add(date '1999-3-01', interval 60 day)
and ws1.ws_ship_date_sk = d_date_sk
and ws1.ws_ship_addr_sk = ca_address_sk
and ca_state = 'OR'
and ws1.ws_web_site_sk = web_site_sk
and web_company_name = 'pri'
and ws1.ws_order_number in (select ws_order_number
                            from ws_wh)
and ws1.ws_order_number in (select wr_order_number
                            from tpcds_2t_baseline.web_returns,ws_wh
                            where wr_order_number = ws_wh.ws_order_number)
order by count(distinct ws_order_number)
limit 100;

-- end query 43 in stream 0 using template query95.tpl
-- start query 44 in stream 0 using template query92.tpl
select  
   sum(ws_ext_discount_amt) as excess_discount_amount 
from 
    tpcds_2t_baseline.web_sales 
   ,tpcds_2t_baseline.item 
   ,tpcds_2t_baseline.date_dim
where
i_manufact_id = 783
and i_item_sk = ws_item_sk 
and d_date between date(1999, 03, 21) and 
        date_add(date '1999-03-21', interval 90 day)
and d_date_sk = ws_sold_date_sk 
and ws_ext_discount_amt  
     > ( 
         SELECT 
            1.3 * avg(ws_ext_discount_amt) 
         FROM 
            tpcds_2t_baseline.web_sales 
           ,tpcds_2t_baseline.date_dim
         WHERE 
              ws_item_sk = i_item_sk 
          and d_date between date(1999, 03, 21) and 
              date_add(date '1999-03-21', interval 90 day)
          and d_date_sk = ws_sold_date_sk 
      ) 
order by sum(ws_ext_discount_amt)
limit 100;

-- end query 44 in stream 0 using template query92.tpl
-- start query 45 in stream 0 using template query3.tpl
select  dt.d_year 
       ,item.i_brand_id brand_id 
       ,item.i_brand brand
       ,sum(ss_sales_price) sum_agg
 from  tpcds_2t_baseline.date_dim dt 
      ,tpcds_2t_baseline.store_sales
      ,tpcds_2t_baseline.item
 where dt.d_date_sk = store_sales.ss_sold_date_sk
   and store_sales.ss_item_sk = item.i_item_sk
   and item.i_manufact_id = 211
   and dt.d_moy=11
 group by dt.d_year
      ,item.i_brand
      ,item.i_brand_id
 order by dt.d_year
         ,sum_agg desc
         ,brand_id
 limit 100;

-- end query 45 in stream 0 using template query3.tpl
-- start query 46 in stream 0 using template query51.tpl
with web_v1 as (
select
  ws_item_sk item_sk, d_date,
  sum(sum(ws_sales_price))
      over (partition by ws_item_sk order by d_date rows between unbounded preceding and current row) cume_sales
from tpcds_2t_baseline.web_sales
    ,tpcds_2t_baseline.date_dim
where ws_sold_date_sk=d_date_sk
  and d_month_seq between 1195 and 1195+11
  and ws_item_sk is not NULL
group by ws_item_sk, d_date),
store_v1 as (
select
  ss_item_sk item_sk, d_date,
  sum(sum(ss_sales_price))
      over (partition by ss_item_sk order by d_date rows between unbounded preceding and current row) cume_sales
from tpcds_2t_baseline.store_sales
    ,tpcds_2t_baseline.date_dim
where ss_sold_date_sk=d_date_sk
  and d_month_seq between 1195 and 1195+11
  and ss_item_sk is not NULL
group by ss_item_sk, d_date)
 select  *
from (select item_sk
     ,d_date
     ,web_sales
     ,store_sales
     ,max(web_sales)
         over (partition by item_sk order by d_date rows between unbounded preceding and current row) web_cumulative
     ,max(store_sales)
         over (partition by item_sk order by d_date rows between unbounded preceding and current row) store_cumulative
     from (select case when web.item_sk is not null then web.item_sk else store.item_sk end item_sk
                 ,case when web.d_date is not null then web.d_date else store.d_date end d_date
                 ,web.cume_sales web_sales
                 ,store.cume_sales store_sales
           from web_v1 web full outer join store_v1 store on (web.item_sk = store.item_sk
                                                          and web.d_date = store.d_date)
          )x )y
where web_cumulative > store_cumulative
order by item_sk
        ,d_date
limit 100;

-- end query 46 in stream 0 using template query51.tpl
-- start query 47 in stream 0 using template query35.tpl
select   
  ca_state,
  cd_gender,
  cd_marital_status,
  cd_dep_count,
  count(*) cnt1,
  stddev_samp(cd_dep_count),
  sum(cd_dep_count),
  min(cd_dep_count),
  cd_dep_employed_count,
  count(*) cnt2,
  stddev_samp(cd_dep_employed_count),
  sum(cd_dep_employed_count),
  min(cd_dep_employed_count),
  cd_dep_college_count,
  count(*) cnt3,
  stddev_samp(cd_dep_college_count),
  sum(cd_dep_college_count),
  min(cd_dep_college_count)
 from
  tpcds_2t_baseline.customer c,tpcds_2t_baseline.customer_address ca,tpcds_2t_baseline.customer_demographics
 where
  c.c_current_addr_sk = ca.ca_address_sk and
  cd_demo_sk = c.c_current_cdemo_sk and 
  exists (select *
          from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
          where c.c_customer_sk = ss_customer_sk and
                ss_sold_date_sk = d_date_sk and
                d_year = 2001 and
                d_qoy < 4) and
   (exists (select *
            from tpcds_2t_baseline.web_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = ws_bill_customer_sk and
                  ws_sold_date_sk = d_date_sk and
                  d_year = 2001 and
                  d_qoy < 4) or 
    exists (select * 
            from tpcds_2t_baseline.catalog_sales,tpcds_2t_baseline.date_dim
            where c.c_customer_sk = cs_ship_customer_sk and
                  cs_sold_date_sk = d_date_sk and
                  d_year = 2001 and
                  d_qoy < 4))
 group by ca_state,
          cd_gender,
          cd_marital_status,
          cd_dep_count,
          cd_dep_employed_count,
          cd_dep_college_count
 order by ca_state,
          cd_gender,
          cd_marital_status,
          cd_dep_count,
          cd_dep_employed_count,
          cd_dep_college_count
 limit 100;

-- end query 47 in stream 0 using template query35.tpl
-- start query 48 in stream 0 using template query49.tpl
select  channel, item, return_ratio, return_rank, currency_rank from
 (select
 'web' as channel
 ,web.item
 ,web.return_ratio
 ,web.return_rank
 ,web.currency_rank
 from (
 	select 
 	 item
 	,return_ratio
 	,currency_ratio
 	,rank() over (order by return_ratio) as return_rank
 	,rank() over (order by currency_ratio) as currency_rank
 	from
 	(	select ws.ws_item_sk as item
 		,(cast(sum(coalesce(wr.wr_return_quantity,0)) as numeric)/
 		cast(sum(coalesce(ws.ws_quantity,0)) as numeric )) as return_ratio
 		,(cast(sum(coalesce(wr.wr_return_amt,0)) as numeric)/
 		cast(sum(coalesce(ws.ws_net_paid,0)) as numeric)) as currency_ratio
 		from 
 		 tpcds_2t_baseline.web_sales ws left outer join tpcds_2t_baseline.web_returns wr 
 			on (ws.ws_order_number = wr.wr_order_number and 
 			ws.ws_item_sk = wr.wr_item_sk)
                 ,tpcds_2t_baseline.date_dim
 		where 
 			wr.wr_return_amt > 10000 
 			and ws.ws_net_profit > 1
                         and ws.ws_net_paid > 0
                         and ws.ws_quantity > 0
                         and ws_sold_date_sk = d_date_sk
                         and d_year = 2000
                         and d_moy = 12
 		group by ws.ws_item_sk
 	) in_web
 ) web
 where 
 (
 web.return_rank <= 10
 or
 web.currency_rank <= 10
 )
 union all
 select 
 'catalog' as channel
 ,catalog.item
 ,catalog.return_ratio
 ,catalog.return_rank
 ,catalog.currency_rank
 from (
 	select 
 	 item
 	,return_ratio
 	,currency_ratio
 	,rank() over (order by return_ratio) as return_rank
 	,rank() over (order by currency_ratio) as currency_rank
 	from
 	(	select 
 		cs.cs_item_sk as item
 		,(cast(sum(coalesce(cr.cr_return_quantity,0)) as numeric)/
 		cast(sum(coalesce(cs.cs_quantity,0)) as numeric)) as return_ratio
 		,(cast(sum(coalesce(cr.cr_return_amount,0)) as numeric)/
 		cast(sum(coalesce(cs.cs_net_paid,0)) as numeric)) as currency_ratio
 		from 
 		tpcds_2t_baseline.catalog_sales cs left outer join tpcds_2t_baseline.catalog_returns cr
 			on (cs.cs_order_number = cr.cr_order_number and 
 			cs.cs_item_sk = cr.cr_item_sk)
                ,tpcds_2t_baseline.date_dim
 		where 
 			cr.cr_return_amount > 10000 
 			and cs.cs_net_profit > 1
                         and cs.cs_net_paid > 0
                         and cs.cs_quantity > 0
                         and cs_sold_date_sk = d_date_sk
                         and d_year = 2000
                         and d_moy = 12
                 group by cs.cs_item_sk
 	) in_cat
 ) catalog
 where 
 (
 catalog.return_rank <= 10
 or
 catalog.currency_rank <=10
 )
 union all
 select 
 'store' as channel
 ,store.item
 ,store.return_ratio
 ,store.return_rank
 ,store.currency_rank
 from (
 	select 
 	 item
 	,return_ratio
 	,currency_ratio
 	,rank() over (order by return_ratio) as return_rank
 	,rank() over (order by currency_ratio) as currency_rank
 	from
 	(	select sts.ss_item_sk as item
 		,(cast(sum(coalesce(sr.sr_return_quantity,0)) as numeric)/cast(sum(coalesce(sts.ss_quantity,0)) as numeric )) as return_ratio
 		,(cast(sum(coalesce(sr.sr_return_amt,0)) as numeric)/cast(sum(coalesce(sts.ss_net_paid,0)) as numeric )) as currency_ratio
 		from 
 		tpcds_2t_baseline.store_sales sts left outer join tpcds_2t_baseline.store_returns sr
 			on (sts.ss_ticket_number = sr.sr_ticket_number and sts.ss_item_sk = sr.sr_item_sk)
                ,tpcds_2t_baseline.date_dim
 		where 
 			sr.sr_return_amt > 10000 
 			and sts.ss_net_profit > 1
                         and sts.ss_net_paid > 0 
                         and sts.ss_quantity > 0
                         and ss_sold_date_sk = d_date_sk
                         and d_year = 2000
                         and d_moy = 12
 		group by sts.ss_item_sk
 	) in_store
 ) store
 where  (
 store.return_rank <= 10
 or 
 store.currency_rank <= 10
 )
 )
 order by 1,4,5,2
 limit 100;

-- end query 48 in stream 0 using template query49.tpl
-- start query 49 in stream 0 using template query9.tpl
select case when (select count(*) 
                  from tpcds_2t_baseline.store_sales 
                  where ss_quantity between 1 and 20) > 144610
            then (select avg(ss_ext_tax) 
                  from tpcds_2t_baseline.store_sales 
                  where ss_quantity between 1 and 20) 
            else (select avg(ss_net_paid)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 1 and 20) end bucket1 ,
       case when (select count(*)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 21 and 40) > 162498
            then (select avg(ss_ext_tax)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 21 and 40) 
            else (select avg(ss_net_paid)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 21 and 40) end bucket2,
       case when (select count(*)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 41 and 60) > 28387
            then (select avg(ss_ext_tax)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 41 and 60)
            else (select avg(ss_net_paid)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 41 and 60) end bucket3,
       case when (select count(*)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 61 and 80) > 442573
            then (select avg(ss_ext_tax)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 61 and 80)
            else (select avg(ss_net_paid)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 61 and 80) end bucket4,
       case when (select count(*)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 81 and 100) > 212532
            then (select avg(ss_ext_tax)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 81 and 100)
            else (select avg(ss_net_paid)
                  from tpcds_2t_baseline.store_sales
                  where ss_quantity between 81 and 100) end bucket5
from tpcds_2t_baseline.reason
where r_reason_sk = 1
;

-- end query 49 in stream 0 using template query9.tpl
-- start query 50 in stream 0 using template query31.tpl
with ss as
 (select ca_county,d_qoy, d_year,sum(ss_ext_sales_price) as store_sales
 from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.customer_address
 where ss_sold_date_sk = d_date_sk
  and ss_addr_sk=ca_address_sk
 group by ca_county,d_qoy, d_year),
 ws as
 (select ca_county,d_qoy, d_year,sum(ws_ext_sales_price) as web_sales
 from tpcds_2t_baseline.web_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.customer_address
 where ws_sold_date_sk = d_date_sk
  and ws_bill_addr_sk=ca_address_sk
 group by ca_county,d_qoy, d_year)
 select 
        ss1.ca_county
       ,ss1.d_year
       ,ws2.web_sales/ws1.web_sales web_q1_q2_increase
       ,ss2.store_sales/ss1.store_sales store_q1_q2_increase
       ,ws3.web_sales/ws2.web_sales web_q2_q3_increase
       ,ss3.store_sales/ss2.store_sales store_q2_q3_increase
 from
        ss ss1
       ,ss ss2
       ,ss ss3
       ,ws ws1
       ,ws ws2
       ,ws ws3
 where
    ss1.d_qoy = 1
    and ss1.d_year = 2000
    and ss1.ca_county = ss2.ca_county
    and ss2.d_qoy = 2
    and ss2.d_year = 2000
 and ss2.ca_county = ss3.ca_county
    and ss3.d_qoy = 3
    and ss3.d_year = 2000
    and ss1.ca_county = ws1.ca_county
    and ws1.d_qoy = 1
    and ws1.d_year = 2000
    and ws1.ca_county = ws2.ca_county
    and ws2.d_qoy = 2
    and ws2.d_year = 2000
    and ws1.ca_county = ws3.ca_county
    and ws3.d_qoy = 3
    and ws3.d_year =2000
    and case when ws1.web_sales > 0 then ws2.web_sales/ws1.web_sales else null end 
       > case when ss1.store_sales > 0 then ss2.store_sales/ss1.store_sales else null end
    and case when ws2.web_sales > 0 then ws3.web_sales/ws2.web_sales else null end
       > case when ss2.store_sales > 0 then ss3.store_sales/ss2.store_sales else null end
 order by web_q2_q3_increase;

-- end query 50 in stream 0 using template query31.tpl
-- start query 51 in stream 0 using template query11.tpl
with year_total as (
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,c_preferred_cust_flag customer_preferred_cust_flag
       ,c_birth_country customer_birth_country
       ,c_login customer_login
       ,c_email_address customer_email_address
       ,d_year dyear
       ,sum(ss_ext_list_price-ss_ext_discount_amt) year_total
       ,'s' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ss_customer_sk
   and ss_sold_date_sk = d_date_sk
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,c_preferred_cust_flag 
         ,c_birth_country
         ,c_login
         ,c_email_address
         ,d_year 
 union all
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,c_preferred_cust_flag customer_preferred_cust_flag
       ,c_birth_country customer_birth_country
       ,c_login customer_login
       ,c_email_address customer_email_address
       ,d_year dyear
       ,sum(ws_ext_list_price-ws_ext_discount_amt) year_total
       ,'w' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.web_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ws_bill_customer_sk
   and ws_sold_date_sk = d_date_sk
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,c_preferred_cust_flag 
         ,c_birth_country
         ,c_login
         ,c_email_address
         ,d_year
         )
  select  
                  t_s_secyear.customer_id
                 ,t_s_secyear.customer_first_name
                 ,t_s_secyear.customer_last_name
                 ,t_s_secyear.customer_preferred_cust_flag
 from year_total t_s_firstyear
     ,year_total t_s_secyear
     ,year_total t_w_firstyear
     ,year_total t_w_secyear
 where t_s_secyear.customer_id = t_s_firstyear.customer_id
         and t_s_firstyear.customer_id = t_w_secyear.customer_id
         and t_s_firstyear.customer_id = t_w_firstyear.customer_id
         and t_s_firstyear.sale_type = 's'
         and t_w_firstyear.sale_type = 'w'
         and t_s_secyear.sale_type = 's'
         and t_w_secyear.sale_type = 'w'
         and t_s_firstyear.dyear = 1998
         and t_s_secyear.dyear = 1998+1
         and t_w_firstyear.dyear = 1998
         and t_w_secyear.dyear = 1998+1
         and t_s_firstyear.year_total > 0
         and t_w_firstyear.year_total > 0
         and case when t_w_firstyear.year_total > 0 then t_w_secyear.year_total / t_w_firstyear.year_total else 0.0 end
             > case when t_s_firstyear.year_total > 0 then t_s_secyear.year_total / t_s_firstyear.year_total else 0.0 end
 order by t_s_secyear.customer_id
         ,t_s_secyear.customer_first_name
         ,t_s_secyear.customer_last_name
         ,t_s_secyear.customer_preferred_cust_flag
limit 100;

-- end query 51 in stream 0 using template query11.tpl
-- start query 52 in stream 0 using template query93.tpl
select  ss_customer_sk
            ,sum(act_sales) sumsales
      from (select ss_item_sk
                  ,ss_ticket_number
                  ,ss_customer_sk
                  ,case when sr_return_quantity is not null then (ss_quantity-sr_return_quantity)*ss_sales_price
                                                            else (ss_quantity*ss_sales_price) end act_sales
            from tpcds_2t_baseline.store_sales left outer join tpcds_2t_baseline.store_returns on (sr_item_sk = ss_item_sk
                                                               and sr_ticket_number = ss_ticket_number)
                ,tpcds_2t_baseline.reason
            where sr_reason_sk = r_reason_sk) t
      group by ss_customer_sk
      order by sumsales, ss_customer_sk
limit 100;

-- end query 52 in stream 0 using template query93.tpl
-- start query 53 in stream 0 using template query29.tpl
select   
     i_item_id
    ,i_item_desc
    ,s_store_id
    ,s_store_name
    ,max(ss_quantity)        as store_sales_quantity
    ,max(sr_return_quantity) as store_returns_quantity
    ,max(cs_quantity)        as catalog_sales_quantity
 from
    tpcds_2t_baseline.store_sales
   ,tpcds_2t_baseline.store_returns
   ,tpcds_2t_baseline.catalog_sales
   ,tpcds_2t_baseline.date_dim             d1
   ,tpcds_2t_baseline.date_dim             d2
   ,tpcds_2t_baseline.date_dim             d3
   ,tpcds_2t_baseline.store
   ,tpcds_2t_baseline.item
 where
     d1.d_moy               = 4 
 and d1.d_year              = 2000
 and d1.d_date_sk           = ss_sold_date_sk
 and i_item_sk              = ss_item_sk
 and s_store_sk             = ss_store_sk
 and ss_customer_sk         = sr_customer_sk
 and ss_item_sk             = sr_item_sk
 and ss_ticket_number       = sr_ticket_number
 and sr_returned_date_sk    = d2.d_date_sk
 and d2.d_moy               between 4 and  4 + 3 
 and d2.d_year              = 2000
 and sr_customer_sk         = cs_bill_customer_sk
 and sr_item_sk             = cs_item_sk
 and cs_sold_date_sk        = d3.d_date_sk     
 and d3.d_year              in (2000,2000+1,2000+2)
 group by
    i_item_id
   ,i_item_desc
   ,s_store_id
   ,s_store_name
 order by
    i_item_id 
   ,i_item_desc
   ,s_store_id
   ,s_store_name
 limit 100;

-- end query 53 in stream 0 using template query29.tpl
-- start query 54 in stream 0 using template query38.tpl
select  count(*) from (
    select distinct c_last_name, c_first_name, d_date
    from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
          where store_sales.ss_sold_date_sk = date_dim.d_date_sk
      and store_sales.ss_customer_sk = customer.c_customer_sk
      and d_month_seq between 1212 and 1212 + 11
  intersect distinct
    select distinct c_last_name, c_first_name, d_date
    from tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
          where catalog_sales.cs_sold_date_sk = date_dim.d_date_sk
      and catalog_sales.cs_bill_customer_sk = customer.c_customer_sk
      and d_month_seq between 1212 and 1212 + 11
  intersect distinct
    select distinct c_last_name, c_first_name, d_date
    from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
          where web_sales.ws_sold_date_sk = date_dim.d_date_sk
      and web_sales.ws_bill_customer_sk = customer.c_customer_sk
      and d_month_seq between 1212 and 1212 + 11
) hot_cust
limit 100;

-- end query 54 in stream 0 using template query38.tpl
-- start query 55 in stream 0 using template query22.tpl
select  i_product_name
             ,i_brand
             ,i_class
             ,i_category
             ,avg(inv_quantity_on_hand) qoh
       from tpcds_2t_baseline.inventory
           ,tpcds_2t_baseline.date_dim
           ,tpcds_2t_baseline.item
       where inv_date_sk=d_date_sk
              and inv_item_sk=i_item_sk
              and d_month_seq between 1188 and 1188 + 11
       group by rollup(i_product_name
                       ,i_brand
                       ,i_class
                       ,i_category)
order by qoh, i_product_name, i_brand, i_class, i_category
limit 100;

-- end query 55 in stream 0 using template query22.tpl
-- start query 56 in stream 0 using template query89.tpl
select  *
from(
select i_category, i_class, i_brand,
       s_store_name, s_company_name,
       d_moy,
       sum(ss_sales_price) sum_sales,
       avg(sum(ss_sales_price)) over
         (partition by i_category, i_brand, s_store_name, s_company_name)
         avg_monthly_sales
from tpcds_2t_baseline.item, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store
where ss_item_sk = i_item_sk and
      ss_sold_date_sk = d_date_sk and
      ss_store_sk = s_store_sk and
      d_year in (2001) and
        ((i_category in ('Electronics','Books','Home') and
          i_class in ('scanners','parenting','wallpaper')
         )
      or (i_category in ('Shoes','Sports','Women') and
          i_class in ('kids','archery','dresses') 
        ))
group by i_category, i_class, i_brand,
         s_store_name, s_company_name, d_moy) tmp1
where case when (avg_monthly_sales <> 0) then (abs(sum_sales - avg_monthly_sales) / avg_monthly_sales) else null end > 0.1
order by sum_sales - avg_monthly_sales, s_store_name
limit 100;

-- end query 56 in stream 0 using template query89.tpl
-- start query 57 in stream 0 using template query15.tpl
select  ca_zip
       ,sum(cs_sales_price)
 from tpcds_2t_baseline.catalog_sales
     ,tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.customer_address
     ,tpcds_2t_baseline.date_dim
 where cs_bill_customer_sk = c_customer_sk
 	and c_current_addr_sk = ca_address_sk 
 	and ( substr(ca_zip,1,5) in ('85669', '86197','88274','83405','86475',
                                   '85392', '85460', '80348', '81792')
 	      or ca_state in ('CA','WA','GA')
 	      or cs_sales_price > 500)
 	and cs_sold_date_sk = d_date_sk
 	and d_qoy = 2 and d_year = 2002
 group by ca_zip
 order by ca_zip
 limit 100;

-- end query 57 in stream 0 using template query15.tpl
-- start query 58 in stream 0 using template query6.tpl
select  a.ca_state state, count(*) cnt
 from tpcds_2t_baseline.customer_address a
     ,tpcds_2t_baseline.customer c
     ,tpcds_2t_baseline.store_sales s
     ,tpcds_2t_baseline.date_dim d
     ,tpcds_2t_baseline.item i
 where       a.ca_address_sk = c.c_current_addr_sk
 	and c.c_customer_sk = s.ss_customer_sk
 	and s.ss_sold_date_sk = d.d_date_sk
 	and s.ss_item_sk = i.i_item_sk
 	and d.d_month_seq = 
 	     (select distinct (d_month_seq)
 	      from tpcds_2t_baseline.date_dim
               where d_year = 1998
 	        and d_moy = 6 )
 	and i.i_current_price > 1.2 * 
             (select avg(j.i_current_price) 
 	     from tpcds_2t_baseline.item j 
 	     where j.i_category = i.i_category)
 group by a.ca_state
 having count(*) >= 10
 order by cnt, a.ca_state 
 limit 100;

-- end query 58 in stream 0 using template query6.tpl
-- start query 59 in stream 0 using template query52.tpl
select  dt.d_year
 	,item.i_brand_id brand_id
 	,item.i_brand brand
 	,sum(ss_ext_sales_price) ext_price
 from tpcds_2t_baseline.date_dim dt
     ,tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.item
 where dt.d_date_sk = store_sales.ss_sold_date_sk
    and store_sales.ss_item_sk = item.i_item_sk
    and item.i_manager_id = 1
    and dt.d_moy=12
    and dt.d_year=2002
 group by dt.d_year
 	,item.i_brand
 	,item.i_brand_id
 order by dt.d_year
 	,ext_price desc
 	,brand_id
limit 100 ;

-- end query 59 in stream 0 using template query52.tpl
-- start query 60 in stream 0 using template query50.tpl
select  
   s_store_name
  ,s_company_id
  ,s_street_number
  ,s_street_name
  ,s_street_type
  ,s_suite_number
  ,s_city
  ,s_county
  ,s_state
  ,s_zip
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk <= 30 ) then 1 else 0 end)  as _30_days 
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 30) and 
                 (sr_returned_date_sk - ss_sold_date_sk <= 60) then 1 else 0 end )  as _31_to_60_days 
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 60) and 
                 (sr_returned_date_sk - ss_sold_date_sk <= 90) then 1 else 0 end)  as _61_to_90_days 
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk > 90) and
                 (sr_returned_date_sk - ss_sold_date_sk <= 120) then 1 else 0 end)  as _91_to_120_days 
  ,sum(case when (sr_returned_date_sk - ss_sold_date_sk  > 120) then 1 else 0 end)  as over_120_days 
from
   tpcds_2t_baseline.store_sales
  ,tpcds_2t_baseline.store_returns
  ,tpcds_2t_baseline.store
  ,tpcds_2t_baseline.date_dim d1
  ,tpcds_2t_baseline.date_dim d2
where
    d2.d_year = 2002
and d2.d_moy  = 8
and ss_ticket_number = sr_ticket_number
and ss_item_sk = sr_item_sk
and ss_sold_date_sk   = d1.d_date_sk
and sr_returned_date_sk   = d2.d_date_sk
and ss_customer_sk = sr_customer_sk
and ss_store_sk = s_store_sk
group by
   s_store_name
  ,s_company_id
  ,s_street_number
  ,s_street_name
  ,s_street_type
  ,s_suite_number
  ,s_city
  ,s_county
  ,s_state
  ,s_zip
order by s_store_name
        ,s_company_id
        ,s_street_number
        ,s_street_name
        ,s_street_type
        ,s_suite_number
        ,s_city
        ,s_county
        ,s_state
        ,s_zip
limit 100;

-- end query 60 in stream 0 using template query50.tpl
-- start query 61 in stream 0 using template query42.tpl
select  dt.d_year
 	,item.i_category_id
 	,item.i_category
 	,sum(ss_ext_sales_price)
 from 	tpcds_2t_baseline.date_dim dt
 	,tpcds_2t_baseline.store_sales
 	,tpcds_2t_baseline.item
 where dt.d_date_sk = store_sales.ss_sold_date_sk
 	and store_sales.ss_item_sk = item.i_item_sk
 	and item.i_manager_id = 1  	
 	and dt.d_moy=11
 	and dt.d_year=1999
 group by 	dt.d_year
 		,item.i_category_id
 		,item.i_category
 order by       sum(ss_ext_sales_price) desc,dt.d_year
 		,item.i_category_id
 		,item.i_category
limit 100 ;

-- end query 61 in stream 0 using template query42.tpl
-- start query 62 in stream 0 using template query41.tpl
select  distinct(i_product_name)
 from tpcds_2t_baseline.item i1
 where i_manufact_id between 794 and 794+40 
   and (select count(*) as item_cnt
        from tpcds_2t_baseline.item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'pink' or i_color = 'yellow') and 
        (i_units = 'Lb' or i_units = 'Pallet') and
        (i_size = 'small' or i_size = 'petite')
        ) or
        (i_category = 'Women' and
        (i_color = 'deep' or i_color = 'goldenrod') and
        (i_units = 'Bundle' or i_units = 'Oz') and
        (i_size = 'extra large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'peru' or i_color = 'cream') and
        (i_units = 'Case' or i_units = 'Ounce') and
        (i_size = 'medium' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'purple' or i_color = 'floral') and
        (i_units = 'Each' or i_units = 'Cup') and
        (i_size = 'small' or i_size = 'petite')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'blue' or i_color = 'seashell') and 
        (i_units = 'Pound' or i_units = 'Carton') and
        (i_size = 'small' or i_size = 'petite')
        ) or
        (i_category = 'Women' and
        (i_color = 'slate' or i_color = 'saddle') and
        (i_units = 'Gram' or i_units = 'Tsp') and
        (i_size = 'extra large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'midnight' or i_color = 'chiffon') and
        (i_units = 'Box' or i_units = 'Ton') and
        (i_size = 'medium' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'orchid' or i_color = 'magenta') and
        (i_units = 'Unknown' or i_units = 'Tbl') and
        (i_size = 'small' or i_size = 'petite')
        )))) > 0
 order by i_product_name
 limit 100;

-- end query 62 in stream 0 using template query41.tpl
-- start query 63 in stream 0 using template query8.tpl
select  s_store_name
      ,sum(ss_net_profit)
 from tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.date_dim
     ,tpcds_2t_baseline.store,
     (select ca_zip
     from (
      SELECT substr(ca_zip,1,5) ca_zip
      FROM tpcds_2t_baseline.customer_address
      WHERE substr(ca_zip,1,5) IN (
                          '43758','76357','20728','59309','19777','27690',
                          '23681','52275','64367','24674','79465',
                          '52936','53936','91889','89248','70394',
                          '66020','56289','45541','29900','99055',
                          '47395','16654','26748','74456','31039',
                          '77674','87076','92273','31667','20150',
                          '84426','75885','61588','57973','29487',
                          '95008','65615','24339','84923','38463',
                          '13811','44227','18570','40389','14584',
                          '33007','61590','47363','57853','43499',
                          '90755','47141','14392','33991','77031',
                          '22854','20127','10624','15730','75295',
                          '98460','17059','26953','82996','17095',
                          '53227','34618','86978','33613','12541',
                          '63977','53929','55459','11516','85350',
                          '99888','23506','10569','66837','50031',
                          '28282','83901','98554','54828','14616',
                          '12743','42473','95507','30542','12883',
                          '95097','61307','32530','37753','53116',
                          '10989','87430','22114','68848','21246',
                          '68327','28446','85870','11697','30541',
                          '22933','70727','17570','55311','73355',
                          '16347','61573','81229','95480','92091',
                          '52603','51232','62666','12173','31993',
                          '98202','78325','46798','63259','34167',
                          '50435','56182','29390','51732','88435',
                          '10366','46637','69283','18218','33324',
                          '24139','16122','53142','16832','98386',
                          '41451','85109','32534','83953','76537',
                          '60857','59939','22271','38788','26296',
                          '59937','14272','98651','38185','16322',
                          '13735','56321','81398','36035','36512',
                          '96290','40596','22748','77965','28512',
                          '15540','20574','72340','81870','31905',
                          '18121','26282','30345','38703','74274',
                          '71129','23244','68810','10106','55461',
                          '25528','71474','37071','21552','81846',
                          '64930','13233','11694','17829','43790',
                          '60379','11482','22714','40977','73320',
                          '13928','78952','92802','66663','95765',
                          '86101','19813','90867','81258','93891',
                          '32755','21548','36452','50931','95773',
                          '57046','14736','30562','44667','80519',
                          '99886','97296','38505','29732','38693',
                          '83898','88032','64442','25944','39303',
                          '70781','92448','64252','89641','88070',
                          '38159','27654','72120','41689','37122',
                          '63776','90416','28479','14787','18038',
                          '39783','50062','28010','13042','86777',
                          '32380','80664','33558','43641','14627',
                          '68858','57733','53458','73016','76141',
                          '42375','12248','38778','50092','80825',
                          '58934','12145','78407','57009','52782',
                          '72140','35635','63926','35282','29292',
                          '30149','33576','95945','48303','56310',
                          '32214','69726','48249','91163','57311',
                          '12361','20491','13551','61620','59648',
                          '44466','53607','18410','99090','37973',
                          '17986','80713','95948','35103','51799',
                          '54707','52269','86117','44909','15530',
                          '28999','80844','62823','46487','15144',
                          '51445','81050','34943','45141','28541',
                          '12414','56922','50548','16422','16780',
                          '53104','60629','24405','61768','48257',
                          '92852','27390','24411','17776','81487',
                          '34848','45773','64188','24209','55276',
                          '11379','33956','46173','67361','32337',
                          '82112','73196','38461','43987','17980',
                          '65414','12247','42107','15326','73018',
                          '59993','85526','50231','60176','23889',
                          '88012','27859','44921','50915','21742',
                          '21272','64763','78761','62002','18502',
                          '42208','49675','69413','46013','67034',
                          '52739','94050','76249','25105','67299',
                          '77588','50637','14333','39372','98030',
                          '79792','12014','56236','61057','51347',
                          '87879','71564','48478','33078','23325',
                          '25526','52855','27570','78396','18695',
                          '24397','76087','35195','97232','29136',
                          '15812','18408','40746','78749')
     intersect distinct
      select ca_zip
      from (SELECT substr(ca_zip,1,5) ca_zip,count(*) cnt
            FROM tpcds_2t_baseline.customer_address, tpcds_2t_baseline.customer
            WHERE ca_address_sk = c_current_addr_sk and
                  c_preferred_cust_flag='Y'
            group by ca_zip
            having count(*) > 10)A1)A2) V1
 where ss_store_sk = s_store_sk
  and ss_sold_date_sk = d_date_sk
  and d_qoy = 1 and d_year = 2000
  and (substr(s_zip,1,2) = substr(V1.ca_zip,1,2))
 group by s_store_name
 order by s_store_name
 limit 100;

-- end query 63 in stream 0 using template query8.tpl
-- start query 64 in stream 0 using template query12.tpl
select  i_item_id
      ,i_item_desc 
      ,i_category 
      ,i_class 
      ,i_current_price
      ,sum(ws_ext_sales_price) as itemrevenue 
      ,sum(ws_ext_sales_price)*100/sum(sum(ws_ext_sales_price)) over
          (partition by i_class) as revenueratio
from	
	tpcds_2t_baseline.web_sales
    	,tpcds_2t_baseline.item 
    	,tpcds_2t_baseline.date_dim
where 
	ws_item_sk = i_item_sk 
  	and i_category in ('Women', 'Children', 'Books')
  	and ws_sold_date_sk = d_date_sk
	and d_date between date(2001, 02, 28) 
				and date_add(date '2001-02-28', interval 30 day)
group by 
	i_item_id
        ,i_item_desc 
        ,i_category
        ,i_class
        ,i_current_price
order by 
	i_category
        ,i_class
        ,i_item_id
        ,i_item_desc
        ,revenueratio
limit 100;

-- end query 64 in stream 0 using template query12.tpl
-- start query 65 in stream 0 using template query20.tpl
select  i_item_id
       ,i_item_desc 
       ,i_category 
       ,i_class 
       ,i_current_price
       ,sum(cs_ext_sales_price) as itemrevenue 
       ,sum(cs_ext_sales_price)*100/sum(sum(cs_ext_sales_price)) over
           (partition by i_class) as revenueratio
 from	tpcds_2t_baseline.catalog_sales
     ,tpcds_2t_baseline.item 
     ,tpcds_2t_baseline.date_dim
 where cs_item_sk = i_item_sk 
   and i_category in ('Men', 'Home', 'Music')
   and cs_sold_date_sk = d_date_sk
 and d_date between date(1999, 03, 08) 
 				and date_add(date '1999-03-08', interval 30 day)
 group by i_item_id
         ,i_item_desc 
         ,i_category
         ,i_class
         ,i_current_price
 order by i_category
         ,i_class
         ,i_item_id
         ,i_item_desc
         ,revenueratio
limit 100;

-- end query 65 in stream 0 using template query20.tpl
-- start query 66 in stream 0 using template query88.tpl
select  *
from
 (select count(*) h8_30_to_9
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk   
     and ss_hdemo_sk = household_demographics.hd_demo_sk 
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 8
     and time_dim.t_minute >= 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2)) 
     and store.s_store_name = 'ese') s1,
 (select count(*) h9_to_9_30 
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk 
     and time_dim.t_hour = 9 
     and time_dim.t_minute < 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s2,
 (select count(*) h9_30_to_10 
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 9
     and time_dim.t_minute >= 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s3,
 (select count(*) h10_to_10_30
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 10 
     and time_dim.t_minute < 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s4,
 (select count(*) h10_30_to_11
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 10 
     and time_dim.t_minute >= 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s5,
 (select count(*) h11_to_11_30
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk 
     and time_dim.t_hour = 11
     and time_dim.t_minute < 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s6,
 (select count(*) h11_30_to_12
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 11
     and time_dim.t_minute >= 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s7,
 (select count(*) h12_to_12_30
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.household_demographics , tpcds_2t_baseline.time_dim, tpcds_2t_baseline.store
 where ss_sold_time_sk = time_dim.t_time_sk
     and ss_hdemo_sk = household_demographics.hd_demo_sk
     and ss_store_sk = s_store_sk
     and time_dim.t_hour = 12
     and time_dim.t_minute < 30
     and ((household_demographics.hd_dep_count = -1 and household_demographics.hd_vehicle_count<=-1+2) or
          (household_demographics.hd_dep_count = 0 and household_demographics.hd_vehicle_count<=0+2) or
          (household_demographics.hd_dep_count = 2 and household_demographics.hd_vehicle_count<=2+2))
     and store.s_store_name = 'ese') s8
;

-- end query 66 in stream 0 using template query88.tpl
-- start query 67 in stream 0 using template query82.tpl
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from tpcds_2t_baseline.item, tpcds_2t_baseline.inventory, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store_sales
 where i_current_price between 9 and 9+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between date(2001, 06, 07) and date_add(date '2001-06-07', interval 60 day)
 and i_manufact_id in (797,412,331,589)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;

-- end query 67 in stream 0 using template query82.tpl
-- start query 68 in stream 0 using template query23.tpl
with frequent_ss_items as
 (select substr(i_item_desc,1,30) itemdesc,i_item_sk item_sk,d_date solddate,count(*) cnt
  from tpcds_2t_baseline.store_sales
      ,tpcds_2t_baseline.date_dim
      ,tpcds_2t_baseline.item
  where ss_sold_date_sk = d_date_sk
    and ss_item_sk = i_item_sk
    and d_year in (2000,2000 + 1,2000 + 2,2000 + 3)
  group by itemdesc,i_item_sk,d_date
  having count(*) >4),
 max_store_sales as
 (select max(csales) tpcds_cmax
  from (select c_customer_sk,sum(ss_quantity*ss_sales_price) csales
        from tpcds_2t_baseline.store_sales
            ,tpcds_2t_baseline.customer
            ,tpcds_2t_baseline.date_dim 
        where ss_customer_sk = c_customer_sk
         and ss_sold_date_sk = d_date_sk
         and d_year in (2000,2000+1,2000+2,2000+3)
        group by c_customer_sk)),
 best_ss_customer as
 (select c_customer_sk,sum(ss_quantity*ss_sales_price) ssales
  from tpcds_2t_baseline.store_sales
      ,tpcds_2t_baseline.customer
  where ss_customer_sk = c_customer_sk
  group by c_customer_sk
  having sum(ss_quantity*ss_sales_price) > (95/100.0) * (select
  *
 from max_store_sales))
  select  c_last_name,c_first_name,sales
 from (select c_last_name,c_first_name,sum(cs_quantity*cs_list_price) sales
        from tpcds_2t_baseline.catalog_sales
            ,tpcds_2t_baseline.customer
            ,tpcds_2t_baseline.date_dim 
        where d_year = 2000 
         and d_moy = 7 
         and cs_sold_date_sk = d_date_sk 
         and cs_item_sk in (select item_sk from frequent_ss_items)
         and cs_bill_customer_sk in (select c_customer_sk from best_ss_customer)
         and cs_bill_customer_sk = c_customer_sk 
       group by c_last_name,c_first_name
      union all
      select c_last_name,c_first_name,sum(ws_quantity*ws_list_price) sales
       from tpcds_2t_baseline.web_sales
           ,tpcds_2t_baseline.customer
           ,tpcds_2t_baseline.date_dim 
       where d_year = 2000 
         and d_moy = 7 
         and ws_sold_date_sk = d_date_sk 
         and ws_item_sk in (select item_sk from frequent_ss_items)
         and ws_bill_customer_sk in (select c_customer_sk from best_ss_customer)
         and ws_bill_customer_sk = c_customer_sk
       group by c_last_name,c_first_name) 
     order by c_last_name,c_first_name,sales
  limit 100;

-- end query 68 in stream 0 using template query23.tpl
-- start query 69 in stream 0 using template query14.tpl
with  cross_items as
 (select i_item_sk ss_item_sk
 from tpcds_2t_baseline.item,
 (select iss.i_brand_id brand_id
     ,iss.i_class_id class_id
     ,iss.i_category_id category_id
 from tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.item iss
     ,tpcds_2t_baseline.date_dim d1
 where ss_item_sk = iss.i_item_sk
   and ss_sold_date_sk = d1.d_date_sk
   and d1.d_year between 1999 AND 1999 + 2
 intersect distinct 
 select ics.i_brand_id
     ,ics.i_class_id
     ,ics.i_category_id
 from tpcds_2t_baseline.catalog_sales
     ,tpcds_2t_baseline.item ics
     ,tpcds_2t_baseline.date_dim d2
 where cs_item_sk = ics.i_item_sk
   and cs_sold_date_sk = d2.d_date_sk
   and d2.d_year between 1999 AND 1999 + 2
 intersect distinct
 select iws.i_brand_id
     ,iws.i_class_id
     ,iws.i_category_id
 from tpcds_2t_baseline.web_sales
     ,tpcds_2t_baseline.item iws
     ,tpcds_2t_baseline.date_dim d3
 where ws_item_sk = iws.i_item_sk
   and ws_sold_date_sk = d3.d_date_sk
   and d3.d_year between 1999 AND 1999 + 2)
 where i_brand_id = brand_id
      and i_class_id = class_id
      and i_category_id = category_id
),
 avg_sales as
 (select avg(quantity*list_price) average_sales
  from (select ss_quantity quantity
             ,ss_list_price list_price
       from tpcds_2t_baseline.store_sales
           ,tpcds_2t_baseline.date_dim
       where ss_sold_date_sk = d_date_sk
         and d_year between 1999 and 1999 + 2
       union all 
       select cs_quantity quantity 
             ,cs_list_price list_price
       from tpcds_2t_baseline.catalog_sales
           ,tpcds_2t_baseline.date_dim
       where cs_sold_date_sk = d_date_sk
         and d_year between 1999 and 1999 + 2 
       union all
       select ws_quantity quantity
             ,ws_list_price list_price
       from tpcds_2t_baseline.web_sales
           ,tpcds_2t_baseline.date_dim
       where ws_sold_date_sk = d_date_sk
         and d_year between 1999 and 1999 + 2) x)
  select  channel, i_brand_id,i_class_id,i_category_id,sum(sales), sum(number_sales)
 from(
       select 'store' channel, i_brand_id,i_class_id
             ,i_category_id,sum(ss_quantity*ss_list_price) sales
             , count(*) number_sales
       from tpcds_2t_baseline.store_sales
           ,tpcds_2t_baseline.item
           ,tpcds_2t_baseline.date_dim
       where ss_item_sk in (select ss_item_sk from cross_items)
         and ss_item_sk = i_item_sk
         and ss_sold_date_sk = d_date_sk
         and d_year = 1999+2 
         and d_moy = 11
       group by i_brand_id,i_class_id,i_category_id
       having sum(ss_quantity*ss_list_price) > (select average_sales from avg_sales)
       union all
       select 'catalog' channel, i_brand_id,i_class_id,i_category_id, sum(cs_quantity*cs_list_price) sales, count(*) number_sales
       from tpcds_2t_baseline.catalog_sales
           ,tpcds_2t_baseline.item
           ,tpcds_2t_baseline.date_dim
       where cs_item_sk in (select ss_item_sk from cross_items)
         and cs_item_sk = i_item_sk
         and cs_sold_date_sk = d_date_sk
         and d_year = 1999+2 
         and d_moy = 11
       group by i_brand_id,i_class_id,i_category_id
       having sum(cs_quantity*cs_list_price) > (select average_sales from avg_sales)
       union all
       select 'web' channel, i_brand_id,i_class_id,i_category_id, sum(ws_quantity*ws_list_price) sales , count(*) number_sales
       from tpcds_2t_baseline.web_sales
           ,tpcds_2t_baseline.item
           ,tpcds_2t_baseline.date_dim
       where ws_item_sk in (select ss_item_sk from cross_items)
         and ws_item_sk = i_item_sk
         and ws_sold_date_sk = d_date_sk
         and d_year = 1999+2
         and d_moy = 11
       group by i_brand_id,i_class_id,i_category_id
       having sum(ws_quantity*ws_list_price) > (select average_sales from avg_sales)
 ) y
 group by rollup (channel, i_brand_id,i_class_id,i_category_id)
 order by channel,i_brand_id,i_class_id,i_category_id
 limit 100;
 
-- end query 69 in stream 0 using template query14.tpl
-- start query 70 in stream 0 using template query57.tpl
with v1 as(
 select i_category, i_brand,
        cc_name,
        d_year, d_moy,
        sum(cs_sales_price) sum_sales,
        avg(sum(cs_sales_price)) over
          (partition by i_category, i_brand,
                     cc_name, d_year)
          avg_monthly_sales,
        rank() over
          (partition by i_category, i_brand,
                     cc_name
           order by d_year, d_moy) rn
 from tpcds_2t_baseline.item, tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.call_center
 where cs_item_sk = i_item_sk and
       cs_sold_date_sk = d_date_sk and
       cc_call_center_sk= cs_call_center_sk and
       (
         d_year = 1999 or
         ( d_year = 1999-1 and d_moy =12) or
         ( d_year = 1999+1 and d_moy =1)
       )
 group by i_category, i_brand,
          cc_name , d_year, d_moy),
 v2 as(
 select v1.i_category, v1.i_brand
        ,v1.d_year, v1.d_moy
        ,v1.avg_monthly_sales
        ,v1.sum_sales, v1_lag.sum_sales psum, v1_lead.sum_sales nsum
 from v1, v1 v1_lag, v1 v1_lead
 where v1.i_category = v1_lag.i_category and
       v1.i_category = v1_lead.i_category and
       v1.i_brand = v1_lag.i_brand and
       v1.i_brand = v1_lead.i_brand and
       v1. cc_name = v1_lag. cc_name and
       v1. cc_name = v1_lead. cc_name and
       v1.rn = v1_lag.rn + 1 and
       v1.rn = v1_lead.rn - 1)
  select  *
 from v2
 where  d_year = 1999 and
        avg_monthly_sales > 0 and
        case when avg_monthly_sales > 0 then abs(sum_sales - avg_monthly_sales) / avg_monthly_sales else null end > 0.1
 order by sum_sales - avg_monthly_sales, nsum
 limit 100;

-- end query 70 in stream 0 using template query57.tpl
-- start query 71 in stream 0 using template query65.tpl
select 
	s_store_name,
	i_item_desc,
	sc.revenue,
	i_current_price,
	i_wholesale_cost,
	i_brand
 from tpcds_2t_baseline.store, tpcds_2t_baseline.item,
     (select ss_store_sk, avg(revenue) as ave
 	from
 	    (select  ss_store_sk, ss_item_sk, 
 		     sum(ss_sales_price) as revenue
 		from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim
 		where ss_sold_date_sk = d_date_sk and d_month_seq between 1212 and 1212+11
 		group by ss_store_sk, ss_item_sk) sa
 	group by ss_store_sk) sb,
     (select  ss_store_sk, ss_item_sk, sum(ss_sales_price) as revenue
 	from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim
 	where ss_sold_date_sk = d_date_sk and d_month_seq between 1212 and 1212+11
 	group by ss_store_sk, ss_item_sk) sc
 where sb.ss_store_sk = sc.ss_store_sk and 
       sc.revenue <= 0.1 * sb.ave and
       s_store_sk = sc.ss_store_sk and
       i_item_sk = sc.ss_item_sk
 order by s_store_name, i_item_desc
limit 100;

-- end query 71 in stream 0 using template query65.tpl
-- start query 72 in stream 0 using template query71.tpl
select i_brand_id brand_id, i_brand brand,t_hour,t_minute,
 	sum(ext_price) ext_price
 from tpcds_2t_baseline.item, (select ws_ext_sales_price as ext_price, 
                        ws_sold_date_sk as sold_date_sk,
                        ws_item_sk as sold_item_sk,
                        ws_sold_time_sk as time_sk  
                 from tpcds_2t_baseline.web_sales,tpcds_2t_baseline.date_dim
                 where d_date_sk = ws_sold_date_sk
                   and d_moy=12
                   and d_year=2002
                 union all
                 select cs_ext_sales_price as ext_price,
                        cs_sold_date_sk as sold_date_sk,
                        cs_item_sk as sold_item_sk,
                        cs_sold_time_sk as time_sk
                 from tpcds_2t_baseline.catalog_sales,tpcds_2t_baseline.date_dim
                 where d_date_sk = cs_sold_date_sk
                   and d_moy=12
                   and d_year=2002
                 union all
                 select ss_ext_sales_price as ext_price,
                        ss_sold_date_sk as sold_date_sk,
                        ss_item_sk as sold_item_sk,
                        ss_sold_time_sk as time_sk
                 from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim
                 where d_date_sk = ss_sold_date_sk
                   and d_moy=12
                   and d_year=2002
                 ) tmp,tpcds_2t_baseline.time_dim
 where
   sold_item_sk = i_item_sk
   and i_manager_id=1
   and time_sk = t_time_sk
   and (t_meal_time = 'breakfast' or t_meal_time = 'dinner')
 group by i_brand, i_brand_id,t_hour,t_minute
 order by ext_price desc, i_brand_id
 ;

-- end query 72 in stream 0 using template query71.tpl
-- start query 73 in stream 0 using template query34.tpl
select c_last_name
       ,c_first_name
       ,c_salutation
       ,c_preferred_cust_flag
       ,ss_ticket_number
       ,cnt from
   (select ss_ticket_number
          ,ss_customer_sk
          ,count(*) cnt
    from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.store,tpcds_2t_baseline.household_demographics
    where store_sales.ss_sold_date_sk = date_dim.d_date_sk
    and store_sales.ss_store_sk = store.s_store_sk  
    and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
    and (date_dim.d_dom between 1 and 3 or date_dim.d_dom between 25 and 28)
    and (household_demographics.hd_buy_potential = '1001-5000' or
         household_demographics.hd_buy_potential = '0-500')
    and household_demographics.hd_vehicle_count > 0
    and (case when household_demographics.hd_vehicle_count > 0 
	then household_demographics.hd_dep_count/ household_demographics.hd_vehicle_count 
	else null 
	end)  > 1.2
    and date_dim.d_year in (2000,2000+1,2000+2)
    and store.s_county in ('Williamson County','Walker County','Ziebach County','Ziebach County',
                           'Ziebach County','Ziebach County','Ziebach County','Ziebach County')
    group by ss_ticket_number,ss_customer_sk) dn,tpcds_2t_baseline.customer
    where ss_customer_sk = c_customer_sk
      and cnt between 15 and 20
    order by c_last_name,c_first_name,c_salutation,c_preferred_cust_flag desc, ss_ticket_number;

-- end query 73 in stream 0 using template query34.tpl
-- start query 74 in stream 0 using template query48.tpl
select sum (ss_quantity)
 from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.store, tpcds_2t_baseline.customer_demographics, tpcds_2t_baseline.customer_address, tpcds_2t_baseline.date_dim
 where s_store_sk = ss_store_sk
 and  ss_sold_date_sk = d_date_sk and d_year = 1998
 and  
 (
  (
   cd_demo_sk = ss_cdemo_sk
   and 
   cd_marital_status = 'S'
   and 
   cd_education_status = 'Secondary'
   and 
   ss_sales_price between 100.00 and 150.00  
   )
 or
  (
  cd_demo_sk = ss_cdemo_sk
   and 
   cd_marital_status = 'M'
   and 
   cd_education_status = 'Primary'
   and 
   ss_sales_price between 50.00 and 100.00   
  )
 or 
 (
  cd_demo_sk = ss_cdemo_sk
  and 
   cd_marital_status = 'W'
   and 
   cd_education_status = '2 yr Degree'
   and 
   ss_sales_price between 150.00 and 200.00  
 )
 )
 and
 (
  (
  ss_addr_sk = ca_address_sk
  and
  ca_country = 'United States'
  and
  ca_state in ('ND', 'KY', 'TX')
  and ss_net_profit between 0 and 2000  
  )
 or
  (ss_addr_sk = ca_address_sk
  and
  ca_country = 'United States'
  and
  ca_state in ('WI', 'AR', 'GA')
  and ss_net_profit between 150 and 3000 
  )
 or
  (ss_addr_sk = ca_address_sk
  and
  ca_country = 'United States'
  and
  ca_state in ('NC', 'SD', 'IL')
  and ss_net_profit between 50 and 25000 
  )
 )
;

-- end query 74 in stream 0 using template query48.tpl
-- start query 75 in stream 0 using template query30.tpl
with customer_total_return as
 (select wr_returning_customer_sk as ctr_customer_sk
        ,ca_state as ctr_state, 
 	sum(wr_return_amt) as ctr_total_return
 from tpcds_2t_baseline.web_returns
     ,tpcds_2t_baseline.date_dim
     ,tpcds_2t_baseline.customer_address
 where wr_returned_date_sk = d_date_sk 
   and d_year =2001
   and wr_returning_addr_sk = ca_address_sk 
 group by wr_returning_customer_sk
         ,ca_state)
  select  c_customer_id,c_salutation,c_first_name,c_last_name,c_preferred_cust_flag
       ,c_birth_day,c_birth_month,c_birth_year,c_birth_country,c_login,c_email_address
       ,c_last_review_date_sk,ctr_total_return
 from customer_total_return ctr1
     ,tpcds_2t_baseline.customer_address
     ,tpcds_2t_baseline.customer
 where ctr1.ctr_total_return > (select avg(ctr_total_return)*1.2
 			  from customer_total_return ctr2 
                  	  where ctr1.ctr_state = ctr2.ctr_state)
       and ca_address_sk = c_current_addr_sk
       and ca_state = 'MO'
       and ctr1.ctr_customer_sk = c_customer_sk
 order by c_customer_id,c_salutation,c_first_name,c_last_name,c_preferred_cust_flag
                  ,c_birth_day,c_birth_month,c_birth_year,c_birth_country,c_login,c_email_address
                  ,c_last_review_date_sk,ctr_total_return
limit 100;

-- end query 75 in stream 0 using template query30.tpl
-- start query 76 in stream 0 using template query74.tpl
with year_total as (
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,d_year as year
       ,sum(ss_net_paid) year_total
       ,'s' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ss_customer_sk
   and ss_sold_date_sk = d_date_sk
   and d_year in (1998,1998+1)
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,d_year
 union all
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,d_year as year
       ,sum(ws_net_paid) year_total
       ,'w' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.web_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ws_bill_customer_sk
   and ws_sold_date_sk = d_date_sk
   and d_year in (1998,1998+1)
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,d_year
         )
  select 
        t_s_secyear.customer_id, t_s_secyear.customer_first_name, t_s_secyear.customer_last_name
 from year_total t_s_firstyear
     ,year_total t_s_secyear
     ,year_total t_w_firstyear
     ,year_total t_w_secyear
 where t_s_secyear.customer_id = t_s_firstyear.customer_id
         and t_s_firstyear.customer_id = t_w_secyear.customer_id
         and t_s_firstyear.customer_id = t_w_firstyear.customer_id
         and t_s_firstyear.sale_type = 's'
         and t_w_firstyear.sale_type = 'w'
         and t_s_secyear.sale_type = 's'
         and t_w_secyear.sale_type = 'w'
         and t_s_firstyear.year = 1998
         and t_s_secyear.year = 1998+1
         and t_w_firstyear.year = 1998
         and t_w_secyear.year = 1998+1
         and t_s_firstyear.year_total > 0
         and t_w_firstyear.year_total > 0
         and case when t_w_firstyear.year_total > 0 then t_w_secyear.year_total / t_w_firstyear.year_total else null end
           > case when t_s_firstyear.year_total > 0 then t_s_secyear.year_total / t_s_firstyear.year_total else null end
 order by 2,1,3
limit 100;

-- end query 76 in stream 0 using template query74.tpl
-- start query 77 in stream 0 using template query87.tpl
select count(*) 
from ((select distinct c_last_name, c_first_name, d_date
       from tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
       where store_sales.ss_sold_date_sk = date_dim.d_date_sk
         and store_sales.ss_customer_sk = customer.c_customer_sk
         and d_month_seq between 1212 and 1212+11)
       except distinct
      (select distinct c_last_name, c_first_name, d_date
       from tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
       where catalog_sales.cs_sold_date_sk = date_dim.d_date_sk
         and catalog_sales.cs_bill_customer_sk = customer.c_customer_sk
         and d_month_seq between 1212 and 1212+11)
       except distinct
      (select distinct c_last_name, c_first_name, d_date
       from tpcds_2t_baseline.web_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.customer
       where web_sales.ws_sold_date_sk = date_dim.d_date_sk
         and web_sales.ws_bill_customer_sk = customer.c_customer_sk
         and d_month_seq between 1212 and 1212+11)
) cool_cust
;

-- end query 77 in stream 0 using template query87.tpl
-- start query 78 in stream 0 using template query77.tpl
with ss as
 (select s_store_sk,
         sum(ss_ext_sales_price) as sales,
         sum(ss_net_profit) as profit
 from tpcds_2t_baseline.store_sales,
      tpcds_2t_baseline.date_dim,
      tpcds_2t_baseline.store
 where ss_sold_date_sk = d_date_sk
 and d_date between date(2002, 08, 18)
            and date_add(date '2002-08-18', interval 30 day)
       and ss_store_sk = s_store_sk
 group by s_store_sk)
 ,
 sr as
 (select s_store_sk,
         sum(sr_return_amt) as returns,
         sum(sr_net_loss) as profit_loss
 from tpcds_2t_baseline.store_returns,
      tpcds_2t_baseline.date_dim,
      tpcds_2t_baseline.store
 where sr_returned_date_sk = d_date_sk
 and d_date between date(2002, 08, 18)
            and date_add(date '2002-08-18', interval 30 day)
       and sr_store_sk = s_store_sk
 group by s_store_sk), 
 cs as
 (select cs_call_center_sk,
        sum(cs_ext_sales_price) as sales,
        sum(cs_net_profit) as profit
 from tpcds_2t_baseline.catalog_sales,
      tpcds_2t_baseline.date_dim
 where cs_sold_date_sk = d_date_sk
 and d_date between date(2002, 08, 18)
            and date_add(date '2002-08-18', interval 30 day)
 group by cs_call_center_sk 
 ), 
 cr as
 (select cr_call_center_sk,
         sum(cr_return_amount) as returns,
         sum(cr_net_loss) as profit_loss
 from tpcds_2t_baseline.catalog_returns,
      tpcds_2t_baseline.date_dim
 where cr_returned_date_sk = d_date_sk
and d_date between date(2002, 08, 18)
            and date_add(date '2002-08-18', interval 30 day)
 group by cr_call_center_sk
 ), 
 ws as
 ( select wp_web_page_sk,
        sum(ws_ext_sales_price) as sales,
        sum(ws_net_profit) as profit
 from tpcds_2t_baseline.web_sales,
      tpcds_2t_baseline.date_dim,
      tpcds_2t_baseline.web_page
 where ws_sold_date_sk = d_date_sk
 and d_date between date(2002, 08, 18)
             and date_add(date '2002-08-18', interval 30 day)
       and ws_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk), 
 wr as
 (select wp_web_page_sk,
        sum(wr_return_amt) as returns,
        sum(wr_net_loss) as profit_loss
 from tpcds_2t_baseline.web_returns,
      tpcds_2t_baseline.date_dim,
      tpcds_2t_baseline.web_page
 where wr_returned_date_sk = d_date_sk
       and d_date between date(2002, 08, 18)
                  and date_add(date '2002-08-18', interval 30 day)
       and wr_web_page_sk = wp_web_page_sk
 group by wp_web_page_sk)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , ss.s_store_sk as id
        , sales
        , coalesce(returns, 0) as returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ss left join sr
        on  ss.s_store_sk = sr.s_store_sk
 union all
 select 'catalog channel' as channel
        , cs_call_center_sk as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  cs
       , cr
 union all
 select 'web channel' as channel
        , ws.wp_web_page_sk as id
        , sales
        , coalesce(returns, 0) returns
        , (profit - coalesce(profit_loss,0)) as profit
 from   ws left join wr
        on  ws.wp_web_page_sk = wr.wp_web_page_sk
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;

-- end query 78 in stream 0 using template query77.tpl
-- start query 79 in stream 0 using template query73.tpl
select c_last_name
       ,c_first_name
       ,c_salutation
       ,c_preferred_cust_flag 
       ,ss_ticket_number
       ,cnt from
   (select ss_ticket_number
          ,ss_customer_sk
          ,count(*) cnt
    from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.store,tpcds_2t_baseline.household_demographics
    where store_sales.ss_sold_date_sk = date_dim.d_date_sk
    and store_sales.ss_store_sk = store.s_store_sk  
    and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
    and date_dim.d_dom between 1 and 2 
    and (household_demographics.hd_buy_potential = '1001-5000' or
         household_demographics.hd_buy_potential = 'Unknown')
    and household_demographics.hd_vehicle_count > 0
    and case when household_demographics.hd_vehicle_count > 0 then 
             household_demographics.hd_dep_count/ household_demographics.hd_vehicle_count else null end > 1
    and date_dim.d_year in (1999,1999+1,1999+2)
    and store.s_county in ('Walker County','Williamson County','Ziebach County','Ziebach County')
    group by ss_ticket_number,ss_customer_sk) dj, tpcds_2t_baseline.customer
    where ss_customer_sk = c_customer_sk
      and cnt between 1 and 5
    order by cnt desc, c_last_name asc;

-- end query 79 in stream 0 using template query73.tpl
-- start query 80 in stream 0 using template query84.tpl
select  c_customer_id as customer_id
       , concat(coalesce(c_last_name,''),  ', ', coalesce(c_first_name,'')) as customername
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.customer_address
     ,tpcds_2t_baseline.customer_demographics
     ,tpcds_2t_baseline.household_demographics
     ,tpcds_2t_baseline.income_band
     ,tpcds_2t_baseline.store_returns
 where ca_city	        =  'Fairfield'
   and c_current_addr_sk = ca_address_sk
   and ib_lower_bound   >=  58125
   and ib_upper_bound   <=  58125 + 50000
   and ib_income_band_sk = hd_income_band_sk
   and cd_demo_sk = c_current_cdemo_sk
   and hd_demo_sk = c_current_hdemo_sk
   and sr_cdemo_sk = cd_demo_sk
 order by c_customer_id
 limit 100;

-- end query 80 in stream 0 using template query84.tpl
-- start query 81 in stream 0 using template query54.tpl
with my_customers as (
 select distinct c_customer_sk
        , c_current_addr_sk
 from   
        ( select cs_sold_date_sk sold_date_sk,
                 cs_bill_customer_sk customer_sk,
                 cs_item_sk item_sk
          from   tpcds_2t_baseline.catalog_sales
          union all
          select ws_sold_date_sk sold_date_sk,
                 ws_bill_customer_sk customer_sk,
                 ws_item_sk item_sk
          from   tpcds_2t_baseline.web_sales
         ) cs_or_ws_sales,
         tpcds_2t_baseline.item,
         tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer
 where   sold_date_sk = d_date_sk
         and item_sk = i_item_sk
         and i_category = 'Children'
         and i_class = 'toddlers'
         and c_customer_sk = cs_or_ws_sales.customer_sk
         and d_moy = 4
         and d_year = 1999
 )
 , my_revenue as (
 select c_customer_sk,
        sum(ss_ext_sales_price) as revenue
 from   my_customers,
        tpcds_2t_baseline.store_sales,
        tpcds_2t_baseline.customer_address,
        tpcds_2t_baseline.store,
        tpcds_2t_baseline.date_dim
 where  c_current_addr_sk = ca_address_sk
        and ca_county = s_county
        and ca_state = s_state
        and ss_sold_date_sk = d_date_sk
        and c_customer_sk = ss_customer_sk
        and d_month_seq between (select distinct d_month_seq+1
                                 from   tpcds_2t_baseline.date_dim where d_year = 1999 and d_moy = 4)
                           and  (select distinct d_month_seq+3
                                 from   tpcds_2t_baseline.date_dim where d_year = 1999 and d_moy = 4)
 group by c_customer_sk
 )
 , segments as
 (select cast((revenue/50) as int64) as segment
  from   my_revenue
 )
  select  segment, count(*) as num_customers, segment*50 as segment_base
 from segments
 group by segment
 order by segment, num_customers
 limit 100;

-- end query 81 in stream 0 using template query54.tpl
-- start query 82 in stream 0 using template query55.tpl
select  i_brand_id brand_id, i_brand brand,
 	sum(ss_ext_sales_price) ext_price
 from tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.item
 where d_date_sk = ss_sold_date_sk
 	and ss_item_sk = i_item_sk
 	and i_manager_id=76
 	and d_moy=12
 	and d_year=1999
 group by i_brand, i_brand_id
 order by ext_price desc, i_brand_id
limit 100 ;

-- end query 82 in stream 0 using template query55.tpl
-- start query 83 in stream 0 using template query56.tpl
with ss as (
 select i_item_id,sum(ss_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.store_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where i_item_id in (select
     i_item_id
from tpcds_2t_baseline.item
where i_color in ('blush','hot','orange'))
 and     ss_item_sk              = i_item_sk
 and     ss_sold_date_sk         = d_date_sk
 and     d_year                  = 2000
 and     d_moy                   = 5
 and     ss_addr_sk              = ca_address_sk
 and     ca_gmt_offset           = -5 
 group by i_item_id),
 cs as (
 select i_item_id,sum(cs_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.catalog_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_item_id               in (select
  i_item_id
from tpcds_2t_baseline.item
where i_color in ('blush','hot','orange'))
 and     cs_item_sk              = i_item_sk
 and     cs_sold_date_sk         = d_date_sk
 and     d_year                  = 2000
 and     d_moy                   = 5
 and     cs_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -5 
 group by i_item_id),
 ws as (
 select i_item_id,sum(ws_ext_sales_price) total_sales
 from
 	tpcds_2t_baseline.web_sales,
 	tpcds_2t_baseline.date_dim,
         tpcds_2t_baseline.customer_address,
         tpcds_2t_baseline.item
 where
         i_item_id               in (select
  i_item_id
from tpcds_2t_baseline.item
where i_color in ('blush','hot','orange'))
 and     ws_item_sk              = i_item_sk
 and     ws_sold_date_sk         = d_date_sk
 and     d_year                  = 2000
 and     d_moy                   = 5
 and     ws_bill_addr_sk         = ca_address_sk
 and     ca_gmt_offset           = -5
 group by i_item_id)
  select  i_item_id ,sum(total_sales) total_sales
 from  (select * from ss 
        union all
        select * from cs 
        union all
        select * from ws) tmp1
 group by i_item_id
 order by total_sales,
          i_item_id
 limit 100;

-- end query 83 in stream 0 using template query56.tpl
-- start query 84 in stream 0 using template query2.tpl
with wscs as
 (select sold_date_sk
        ,sales_price
  from (select ws_sold_date_sk sold_date_sk
              ,ws_ext_sales_price sales_price
        from tpcds_2t_baseline.web_sales 
        union all
        select cs_sold_date_sk sold_date_sk
              ,cs_ext_sales_price sales_price
        from tpcds_2t_baseline.catalog_sales)),
 wswscs as 
 (select d_week_seq,
        sum(case when (d_day_name='Sunday') then sales_price else null end) sun_sales,
        sum(case when (d_day_name='Monday') then sales_price else null end) mon_sales,
        sum(case when (d_day_name='Tuesday') then sales_price else  null end) tue_sales,
        sum(case when (d_day_name='Wednesday') then sales_price else null end) wed_sales,
        sum(case when (d_day_name='Thursday') then sales_price else null end) thu_sales,
        sum(case when (d_day_name='Friday') then sales_price else null end) fri_sales,
        sum(case when (d_day_name='Saturday') then sales_price else null end) sat_sales
 from wscs
     ,tpcds_2t_baseline.date_dim
 where d_date_sk = sold_date_sk
 group by d_week_seq)
 select d_week_seq1
       ,round(sun_sales1/sun_sales2,2)
       ,round(mon_sales1/mon_sales2,2)
       ,round(tue_sales1/tue_sales2,2)
       ,round(wed_sales1/wed_sales2,2)
       ,round(thu_sales1/thu_sales2,2)
       ,round(fri_sales1/fri_sales2,2)
       ,round(sat_sales1/sat_sales2,2)
 from
 (select wswscs.d_week_seq d_week_seq1
        ,sun_sales sun_sales1
        ,mon_sales mon_sales1
        ,tue_sales tue_sales1
        ,wed_sales wed_sales1
        ,thu_sales thu_sales1
        ,fri_sales fri_sales1
        ,sat_sales sat_sales1
  from wswscs,tpcds_2t_baseline.date_dim 
  where date_dim.d_week_seq = wswscs.d_week_seq and
        d_year = 1998) y,
 (select wswscs.d_week_seq d_week_seq2
        ,sun_sales sun_sales2
        ,mon_sales mon_sales2
        ,tue_sales tue_sales2
        ,wed_sales wed_sales2
        ,thu_sales thu_sales2
        ,fri_sales fri_sales2
        ,sat_sales sat_sales2
  from wswscs
      ,tpcds_2t_baseline.date_dim 
  where date_dim.d_week_seq = wswscs.d_week_seq and
        d_year = 1998+1) z
 where d_week_seq1=d_week_seq2-53
 order by d_week_seq1;

-- end query 84 in stream 0 using template query2.tpl
-- start query 85 in stream 0 using template query26.tpl
select  i_item_id, 
        avg(cs_quantity) agg1,
        avg(cs_list_price) agg2,
        avg(cs_coupon_amt) agg3,
        avg(cs_sales_price) agg4 
 from tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.customer_demographics, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.item, tpcds_2t_baseline.promotion
 where cs_sold_date_sk = d_date_sk and
       cs_item_sk = i_item_sk and
       cs_bill_cdemo_sk = cd_demo_sk and
       cs_promo_sk = p_promo_sk and
       cd_gender = 'M' and 
       cd_marital_status = 'S' and
       cd_education_status = '4 yr Degree' and
       (p_channel_email = 'N' or p_channel_event = 'N') and
       d_year = 1999 
 group by i_item_id
 order by i_item_id
 limit 100;

-- end query 85 in stream 0 using template query26.tpl
-- start query 86 in stream 0 using template query40.tpl
select  
   w_state
  ,i_item_id
  ,sum(case when d_date < date(1998, 03, 13) 
 		then cs_sales_price - coalesce(cr_refunded_cash,0) else 0 end) as sales_before
  ,sum(case when d_date >= date(1998, 03, 13) 
 		then cs_sales_price - coalesce(cr_refunded_cash,0) else 0 end) as sales_after
 from
   tpcds_2t_baseline.catalog_sales left outer join tpcds_2t_baseline.catalog_returns on
       (cs_order_number = cr_order_number 
        and cs_item_sk = cr_item_sk)
  ,tpcds_2t_baseline.warehouse 
  ,tpcds_2t_baseline.item
  ,tpcds_2t_baseline.date_dim
 where
     i_current_price between 0.99 and 1.49
 and i_item_sk          = cs_item_sk
 and cs_warehouse_sk    = w_warehouse_sk 
 and cs_sold_date_sk    = d_date_sk
 and d_date between date_sub(date '1998-03-13', interval 30 day)
                and date_add(date '1998-03-13', interval 30 day) 
 group by
    w_state,i_item_id
 order by w_state,i_item_id
limit 100;

-- end query 86 in stream 0 using template query40.tpl
-- start query 87 in stream 0 using template query72.tpl
select  i_item_desc
      ,w_warehouse_name
      ,d1.d_week_seq
      ,sum(case when p_promo_sk is null then 1 else 0 end) no_promo
      ,sum(case when p_promo_sk is not null then 1 else 0 end) promo
      ,count(*) total_cnt
from tpcds_2t_baseline.catalog_sales
join tpcds_2t_baseline.inventory on (cs_item_sk = inv_item_sk)
join tpcds_2t_baseline.warehouse on (w_warehouse_sk=inv_warehouse_sk)
join tpcds_2t_baseline.item on (i_item_sk = cs_item_sk)
join tpcds_2t_baseline.customer_demographics on (cs_bill_cdemo_sk = cd_demo_sk)
join tpcds_2t_baseline.household_demographics on (cs_bill_hdemo_sk = hd_demo_sk)
join tpcds_2t_baseline.date_dim d1 on (cs_sold_date_sk = d1.d_date_sk)
join tpcds_2t_baseline.date_dim d2 on (inv_date_sk = d2.d_date_sk)
join tpcds_2t_baseline.date_dim d3 on (cs_ship_date_sk = d3.d_date_sk)
left outer join tpcds_2t_baseline.promotion on (cs_promo_sk=p_promo_sk)
left outer join tpcds_2t_baseline.catalog_returns on (cr_item_sk = cs_item_sk and cr_order_number = cs_order_number)
where d1.d_week_seq = d2.d_week_seq
  and inv_quantity_on_hand < cs_quantity 
  and d3.d_date > date_add(d1.d_date, interval 5 day)
  and hd_buy_potential = '501-1000'
  and d1.d_year = 2002
  and cd_marital_status = 'M'
group by i_item_desc,w_warehouse_name,d1.d_week_seq
order by total_cnt desc, i_item_desc, w_warehouse_name, d_week_seq
limit 100;

-- end query 87 in stream 0 using template query72.tpl
-- start query 88 in stream 0 using template query53.tpl
select  * from 
(select i_manufact_id,
sum(ss_sales_price) sum_sales,
avg(sum(ss_sales_price)) over (partition by i_manufact_id) avg_quarterly_sales
from tpcds_2t_baseline.item, tpcds_2t_baseline.store_sales, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.store
where ss_item_sk = i_item_sk and
ss_sold_date_sk = d_date_sk and
ss_store_sk = s_store_sk and
d_month_seq in (1202,1202+1,1202+2,1202+3,1202+4,1202+5,1202+6,1202+7,1202+8,1202+9,1202+10,1202+11) and
((i_category in ('Books','Children','Electronics') and
i_class in ('personal','portable','reference','self-help') and
i_brand in ('scholaramalgamalg #14','scholaramalgamalg #7',
		'exportiunivamalg #9','scholaramalgamalg #9'))
or(i_category in ('Women','Music','Men') and
i_class in ('accessories','classical','fragrances','pants') and
i_brand in ('amalgimporto #1','edu packscholar #1','exportiimporto #1',
		'importoamalg #1')))
group by i_manufact_id, d_qoy ) tmp1
where case when avg_quarterly_sales > 0 
	then abs (sum_sales - avg_quarterly_sales)/ avg_quarterly_sales 
	else null end > 0.1
order by avg_quarterly_sales,
	 sum_sales,
	 i_manufact_id
limit 100;

-- end query 88 in stream 0 using template query53.tpl
-- start query 89 in stream 0 using template query79.tpl
select 
  c_last_name,c_first_name,substr(s_city,1,30),ss_ticket_number,amt,profit
  from
   (select ss_ticket_number
          ,ss_customer_sk
          ,store.s_city
          ,sum(ss_coupon_amt) amt
          ,sum(ss_net_profit) profit
    from tpcds_2t_baseline.store_sales,tpcds_2t_baseline.date_dim,tpcds_2t_baseline.store,tpcds_2t_baseline.household_demographics
    where store_sales.ss_sold_date_sk = date_dim.d_date_sk
    and store_sales.ss_store_sk = store.s_store_sk  
    and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
    and (household_demographics.hd_dep_count = 9 or household_demographics.hd_vehicle_count > -1)
    and date_dim.d_dow = 1
    and date_dim.d_year in (2000,2000+1,2000+2) 
    and store.s_number_employees between 200 and 295
    group by ss_ticket_number,ss_customer_sk,ss_addr_sk,store.s_city) ms, tpcds_2t_baseline.customer
    where ss_customer_sk = c_customer_sk
 order by c_last_name,c_first_name,substr(s_city,1,30), profit
limit 100;

-- end query 89 in stream 0 using template query79.tpl
-- start query 90 in stream 0 using template query18.tpl
select  i_item_id,
        ca_country,
        ca_state, 
        ca_county,
        avg( cast(cs_quantity as numeric)) agg1,
        avg( cast(cs_list_price as numeric)) agg2,
        avg( cast(cs_coupon_amt as numeric)) agg3,
        avg( cast(cs_sales_price as numeric)) agg4,
        avg( cast(cs_net_profit as numeric)) agg5,
        avg( cast(c_birth_year as numeric)) agg6,
        avg( cast(cd1.cd_dep_count as numeric)) agg7
 from tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.customer_demographics cd1, 
      tpcds_2t_baseline.customer_demographics cd2, tpcds_2t_baseline.customer, tpcds_2t_baseline.customer_address, tpcds_2t_baseline.date_dim, tpcds_2t_baseline.item
 where cs_sold_date_sk = d_date_sk and
       cs_item_sk = i_item_sk and
       cs_bill_cdemo_sk = cd1.cd_demo_sk and
       cs_bill_customer_sk = c_customer_sk and
       cd1.cd_gender = 'F' and 
       cd1.cd_education_status = '4 yr Degree' and
       c_current_cdemo_sk = cd2.cd_demo_sk and
       c_current_addr_sk = ca_address_sk and
       c_birth_month in (4,2,12,10,11,3) and
       d_year = 2001 and
       ca_state in ('AR','GA','CO'
                   ,'MS','ND','KS','KY')
 group by rollup (i_item_id, ca_country, ca_state, ca_county)
 order by ca_country,
        ca_state, 
        ca_county,
	i_item_id
 limit 100;

-- end query 90 in stream 0 using template query18.tpl
-- start query 91 in stream 0 using template query13.tpl
select avg(ss_quantity)
       ,avg(ss_ext_sales_price)
       ,avg(ss_ext_wholesale_cost)
       ,sum(ss_ext_wholesale_cost)
 from tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.store
     ,tpcds_2t_baseline.customer_demographics
     ,tpcds_2t_baseline.household_demographics
     ,tpcds_2t_baseline.customer_address
     ,tpcds_2t_baseline.date_dim
 where s_store_sk = ss_store_sk
 and  ss_sold_date_sk = d_date_sk and d_year = 2001
 and((ss_hdemo_sk=hd_demo_sk
  and cd_demo_sk = ss_cdemo_sk
  and cd_marital_status = 'D'
  and cd_education_status = 'Advanced Degree'
  and ss_sales_price between 100.00 and 150.00
  and hd_dep_count = 3   
     )or
     (ss_hdemo_sk=hd_demo_sk
  and cd_demo_sk = ss_cdemo_sk
  and cd_marital_status = 'U'
  and cd_education_status = '2 yr Degree'
  and ss_sales_price between 50.00 and 100.00   
  and hd_dep_count = 1
     ) or 
     (ss_hdemo_sk=hd_demo_sk
  and cd_demo_sk = ss_cdemo_sk
  and cd_marital_status = 'W'
  and cd_education_status = '4 yr Degree'
  and ss_sales_price between 150.00 and 200.00 
  and hd_dep_count = 1  
     ))
 and((ss_addr_sk = ca_address_sk
  and ca_country = 'United States'
  and ca_state in ('TX', 'OH', 'OK')
  and ss_net_profit between 100 and 200  
     ) or
     (ss_addr_sk = ca_address_sk
  and ca_country = 'United States'
  and ca_state in ('MS', 'NY', 'GA')
  and ss_net_profit between 150 and 300  
     ) or
     (ss_addr_sk = ca_address_sk
  and ca_country = 'United States'
  and ca_state in ('TN', 'IN', 'AL')
  and ss_net_profit between 50 and 250  
     ))
;

-- end query 91 in stream 0 using template query13.tpl
-- start query 92 in stream 0 using template query24.tpl
with ssales as
(select c_last_name
      ,c_first_name
      ,s_store_name
      ,ca_state
      ,s_state
      ,i_color
      ,i_current_price
      ,i_manager_id
      ,i_units
      ,i_size
      ,sum(ss_net_profit) netpaid
from tpcds_2t_baseline.store_sales
    ,tpcds_2t_baseline.store_returns
    ,tpcds_2t_baseline.store
    ,tpcds_2t_baseline.item
    ,tpcds_2t_baseline.customer
    ,tpcds_2t_baseline.customer_address
where ss_ticket_number = sr_ticket_number
  and ss_item_sk = sr_item_sk
  and ss_customer_sk = c_customer_sk
  and ss_item_sk = i_item_sk
  and ss_store_sk = s_store_sk
  and c_current_addr_sk = ca_address_sk
  and c_birth_country <> upper(ca_country)
  and s_zip = ca_zip
and s_market_id=10
group by c_last_name
        ,c_first_name
        ,s_store_name
        ,ca_state
        ,s_state
        ,i_color
        ,i_current_price
        ,i_manager_id
        ,i_units
        ,i_size)
select c_last_name
      ,c_first_name
      ,s_store_name
      ,sum(netpaid) paid
from ssales
where i_color = 'firebrick'
group by c_last_name
        ,c_first_name
        ,s_store_name
having sum(netpaid) > (select 0.05*avg(netpaid)
                                 from ssales)
order by c_last_name
        ,c_first_name
        ,s_store_name
;


-- end query 92 in stream 0 using template query24.tpl
-- start query 93 in stream 0 using template query4.tpl
with year_total as (
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,c_preferred_cust_flag customer_preferred_cust_flag
       ,c_birth_country customer_birth_country
       ,c_login customer_login
       ,c_email_address customer_email_address
       ,d_year dyear
       ,sum(((ss_ext_list_price-ss_ext_wholesale_cost-ss_ext_discount_amt)+ss_ext_sales_price)/2) year_total
       ,'s' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.store_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ss_customer_sk
   and ss_sold_date_sk = d_date_sk
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,c_preferred_cust_flag
         ,c_birth_country
         ,c_login
         ,c_email_address
         ,d_year
 union all
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,c_preferred_cust_flag customer_preferred_cust_flag
       ,c_birth_country customer_birth_country
       ,c_login customer_login
       ,c_email_address customer_email_address
       ,d_year dyear
       ,sum((((cs_ext_list_price-cs_ext_wholesale_cost-cs_ext_discount_amt)+cs_ext_sales_price)/2) ) year_total
       ,'c' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.catalog_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = cs_bill_customer_sk
   and cs_sold_date_sk = d_date_sk
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,c_preferred_cust_flag
         ,c_birth_country
         ,c_login
         ,c_email_address
         ,d_year
union all
 select c_customer_id customer_id
       ,c_first_name customer_first_name
       ,c_last_name customer_last_name
       ,c_preferred_cust_flag customer_preferred_cust_flag
       ,c_birth_country customer_birth_country
       ,c_login customer_login
       ,c_email_address customer_email_address
       ,d_year dyear
       ,sum((((ws_ext_list_price-ws_ext_wholesale_cost-ws_ext_discount_amt)+ws_ext_sales_price)/2) ) year_total
       ,'w' sale_type
 from tpcds_2t_baseline.customer
     ,tpcds_2t_baseline.web_sales
     ,tpcds_2t_baseline.date_dim
 where c_customer_sk = ws_bill_customer_sk
   and ws_sold_date_sk = d_date_sk
 group by c_customer_id
         ,c_first_name
         ,c_last_name
         ,c_preferred_cust_flag
         ,c_birth_country
         ,c_login
         ,c_email_address
         ,d_year
         )
  select  
                  t_s_secyear.customer_id
                 ,t_s_secyear.customer_first_name
                 ,t_s_secyear.customer_last_name
                 ,t_s_secyear.customer_preferred_cust_flag
 from year_total t_s_firstyear
     ,year_total t_s_secyear
     ,year_total t_c_firstyear
     ,year_total t_c_secyear
     ,year_total t_w_firstyear
     ,year_total t_w_secyear
 where t_s_secyear.customer_id = t_s_firstyear.customer_id
   and t_s_firstyear.customer_id = t_c_secyear.customer_id
   and t_s_firstyear.customer_id = t_c_firstyear.customer_id
   and t_s_firstyear.customer_id = t_w_firstyear.customer_id
   and t_s_firstyear.customer_id = t_w_secyear.customer_id
   and t_s_firstyear.sale_type = 's'
   and t_c_firstyear.sale_type = 'c'
   and t_w_firstyear.sale_type = 'w'
   and t_s_secyear.sale_type = 's'
   and t_c_secyear.sale_type = 'c'
   and t_w_secyear.sale_type = 'w'
   and t_s_firstyear.dyear =  1999
   and t_s_secyear.dyear = 1999+1
   and t_c_firstyear.dyear =  1999
   and t_c_secyear.dyear =  1999+1
   and t_w_firstyear.dyear = 1999
   and t_w_secyear.dyear = 1999+1
   and t_s_firstyear.year_total > 0
   and t_c_firstyear.year_total > 0
   and t_w_firstyear.year_total > 0
   and case when t_c_firstyear.year_total > 0 then t_c_secyear.year_total / t_c_firstyear.year_total else null end
           > case when t_s_firstyear.year_total > 0 then t_s_secyear.year_total / t_s_firstyear.year_total else null end
   and case when t_c_firstyear.year_total > 0 then t_c_secyear.year_total / t_c_firstyear.year_total else null end
           > case when t_w_firstyear.year_total > 0 then t_w_secyear.year_total / t_w_firstyear.year_total else null end
 order by t_s_secyear.customer_id
         ,t_s_secyear.customer_first_name
         ,t_s_secyear.customer_last_name
         ,t_s_secyear.customer_preferred_cust_flag
limit 100;

-- end query 93 in stream 0 using template query4.tpl
-- start query 94 in stream 0 using template query99.tpl
select  
   substr(w_warehouse_name,1,20) as warehouse_name
  ,sm_type
  ,cc_name
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk <= 30 ) then 1 else 0 end)  as _30_days 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 30) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 60) then 1 else 0 end )  as _31_to_60_days 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 60) and 
                 (cs_ship_date_sk - cs_sold_date_sk <= 90) then 1 else 0 end)  as _61_to_90_days 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk > 90) and
                 (cs_ship_date_sk - cs_sold_date_sk <= 120) then 1 else 0 end)  as _91_to_120_days 
  ,sum(case when (cs_ship_date_sk - cs_sold_date_sk  > 120) then 1 else 0 end)  as over_120_days 
from
   tpcds_2t_baseline.catalog_sales
  ,tpcds_2t_baseline.warehouse
  ,tpcds_2t_baseline.ship_mode
  ,tpcds_2t_baseline.call_center
  ,tpcds_2t_baseline.date_dim
where
    d_month_seq between 1222 and 1222 + 11
and cs_ship_date_sk   = d_date_sk
and cs_warehouse_sk   = w_warehouse_sk
and cs_ship_mode_sk   = sm_ship_mode_sk
and cs_call_center_sk = cc_call_center_sk
group by
   warehouse_name
  ,sm_type
  ,cc_name
order by warehouse_name
        ,sm_type
        ,cc_name
limit 100;

-- end query 94 in stream 0 using template query99.tpl
-- start query 95 in stream 0 using template query68.tpl
select  c_last_name
       ,c_first_name
       ,ca_city
       ,bought_city
       ,ss_ticket_number
       ,extended_price
       ,extended_tax
       ,list_price
 from (select ss_ticket_number
             ,ss_customer_sk
             ,ca_city bought_city
             ,sum(ss_ext_sales_price) extended_price 
             ,sum(ss_ext_list_price) list_price
             ,sum(ss_ext_tax) extended_tax 
       from tpcds_2t_baseline.store_sales
           ,tpcds_2t_baseline.date_dim
           ,tpcds_2t_baseline.store
           ,tpcds_2t_baseline.household_demographics
           ,tpcds_2t_baseline.customer_address 
       where store_sales.ss_sold_date_sk = date_dim.d_date_sk
         and store_sales.ss_store_sk = store.s_store_sk  
        and store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk
        and store_sales.ss_addr_sk = customer_address.ca_address_sk
        and date_dim.d_dom between 1 and 2 
        and (household_demographics.hd_dep_count = 6 or
             household_demographics.hd_vehicle_count= 1)
        and date_dim.d_year in (1998,1998+1,1998+2)
        and store.s_city in ('Midway','Pleasant Hill')
       group by ss_ticket_number
               ,ss_customer_sk
               ,ss_addr_sk,ca_city) dn
      ,tpcds_2t_baseline.customer
      ,tpcds_2t_baseline.customer_address current_addr
 where ss_customer_sk = c_customer_sk
   and customer.c_current_addr_sk = current_addr.ca_address_sk
   and current_addr.ca_city <> bought_city
 order by c_last_name
         ,ss_ticket_number
 limit 100;

-- end query 95 in stream 0 using template query68.tpl
-- start query 96 in stream 0 using template query83.tpl
with sr_items as
 (select i_item_id item_id,
        sum(sr_return_quantity) sr_item_qty
 from tpcds_2t_baseline.store_returns,
      tpcds_2t_baseline.item,
      tpcds_2t_baseline.date_dim
 where sr_item_sk = i_item_sk
 and   d_date    in 
	(select d_date
	from tpcds_2t_baseline.date_dim
	where d_week_seq in 
		(select d_week_seq
		from tpcds_2t_baseline.date_dim
	  where d_date in ('1998-05-29','1998-08-19','1998-11-10')))
 and   sr_returned_date_sk   = d_date_sk
 group by i_item_id),
 cr_items as
 (select i_item_id item_id,
        sum(cr_return_quantity) cr_item_qty
 from tpcds_2t_baseline.catalog_returns,
      tpcds_2t_baseline.item,
      tpcds_2t_baseline.date_dim
 where cr_item_sk = i_item_sk
 and   d_date    in 
	(select d_date
	from tpcds_2t_baseline.date_dim
	where d_week_seq in 
		(select d_week_seq
		from tpcds_2t_baseline.date_dim
	  where d_date in ('1998-05-29','1998-08-19','1998-11-10')))
 and   cr_returned_date_sk   = d_date_sk
 group by i_item_id),
 wr_items as
 (select i_item_id item_id,
        sum(wr_return_quantity) wr_item_qty
 from tpcds_2t_baseline.web_returns,
      tpcds_2t_baseline.item,
      tpcds_2t_baseline.date_dim
 where wr_item_sk = i_item_sk
 and   d_date    in 
	(select d_date
	from tpcds_2t_baseline.date_dim
	where d_week_seq in 
		(select d_week_seq
		from tpcds_2t_baseline.date_dim
		where d_date in ('1998-05-29','1998-08-19','1998-11-10')))
 and   wr_returned_date_sk   = d_date_sk
 group by i_item_id)
  select  sr_items.item_id
       ,sr_item_qty
       ,sr_item_qty/(sr_item_qty+cr_item_qty+wr_item_qty)/3.0 * 100 sr_dev
       ,cr_item_qty
       ,cr_item_qty/(sr_item_qty+cr_item_qty+wr_item_qty)/3.0 * 100 cr_dev
       ,wr_item_qty
       ,wr_item_qty/(sr_item_qty+cr_item_qty+wr_item_qty)/3.0 * 100 wr_dev
       ,(sr_item_qty+cr_item_qty+wr_item_qty)/3.0 average
 from sr_items
     ,cr_items
     ,wr_items
 where sr_items.item_id=cr_items.item_id
   and sr_items.item_id=wr_items.item_id 
 order by sr_items.item_id
         ,sr_item_qty
 limit 100;

-- end query 96 in stream 0 using template query83.tpl
-- start query 97 in stream 0 using template query61.tpl
select  promotions,total,cast(promotions as numeric)/cast(total as numeric)*100
from
  (select sum(ss_ext_sales_price) promotions
   from  tpcds_2t_baseline.store_sales
        ,tpcds_2t_baseline.store
        ,tpcds_2t_baseline.promotion
        ,tpcds_2t_baseline.date_dim
        ,tpcds_2t_baseline.customer
        ,tpcds_2t_baseline.customer_address 
        ,tpcds_2t_baseline.item
   where ss_sold_date_sk = d_date_sk
   and   ss_store_sk = s_store_sk
   and   ss_promo_sk = p_promo_sk
   and   ss_customer_sk= c_customer_sk
   and   ca_address_sk = c_current_addr_sk
   and   ss_item_sk = i_item_sk 
   and   ca_gmt_offset = -6
   and   i_category = 'Sports'
   and   (p_channel_dmail = 'Y' or p_channel_email = 'Y' or p_channel_tv = 'Y')
   and   s_gmt_offset = -6
   and   d_year = 1998
   and   d_moy  = 12) promotional_sales,
  (select sum(ss_ext_sales_price) total
   from  tpcds_2t_baseline.store_sales
        ,tpcds_2t_baseline.store
        ,tpcds_2t_baseline.date_dim
        ,tpcds_2t_baseline.customer
        ,tpcds_2t_baseline.customer_address
        ,tpcds_2t_baseline.item
   where ss_sold_date_sk = d_date_sk
   and   ss_store_sk = s_store_sk
   and   ss_customer_sk= c_customer_sk
   and   ca_address_sk = c_current_addr_sk
   and   ss_item_sk = i_item_sk
   and   ca_gmt_offset = -6
   and   i_category = 'Sports'
   and   s_gmt_offset = -6
   and   d_year = 1998
   and   d_moy  = 12) all_sales
order by promotions, total
limit 100;

-- end query 97 in stream 0 using template query61.tpl
-- start query 98 in stream 0 using template query5.tpl
with ssr as
 (select s_store_id,
        sum(sales_price) as sales,
        sum(profit) as profit,
        sum(return_amt) as returns,
        sum(net_loss) as profit_loss
 from
  ( select  ss_store_sk as store_sk,
            ss_sold_date_sk  as date_sk,
            ss_ext_sales_price as sales_price,
            ss_net_profit as profit,
            cast(0 as numeric) as return_amt,
            cast(0 as numeric) as net_loss
    from tpcds_2t_baseline.store_sales
    union all
    select sr_store_sk as store_sk,
           sr_returned_date_sk as date_sk,
           cast(0 as numeric) as sales_price,
           cast(0 as numeric) as profit,
           sr_return_amt as return_amt,
           sr_net_loss as net_loss
    from tpcds_2t_baseline.store_returns
   ) salesreturns,
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.store
 where date_sk = d_date_sk
       and d_date between date(1998, 08, 21) 
                  and date_add(date '1998-08-21', interval 14 day)
       and store_sk = s_store_sk
 group by s_store_id)
 ,
 csr as
 (select cp_catalog_page_id,
        sum(sales_price) as sales,
        sum(profit) as profit,
        sum(return_amt) as returns,
        sum(net_loss) as profit_loss
 from
  ( select  cs_catalog_page_sk as page_sk,
            cs_sold_date_sk  as date_sk,
            cs_ext_sales_price as sales_price,
            cs_net_profit as profit,
            cast(0 as numeric) as return_amt,
            cast(0 as numeric) as net_loss
    from tpcds_2t_baseline.catalog_sales
    union all
    select cr_catalog_page_sk as page_sk,
           cr_returned_date_sk as date_sk,
           cast(0 as numeric) as sales_price,
           cast(0 as numeric) as profit,
           cr_return_amount as return_amt,
           cr_net_loss as net_loss
    from tpcds_2t_baseline.catalog_returns
   ) salesreturns,
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.catalog_page
 where date_sk = d_date_sk
       and d_date between date(1998, 08, 21)
                  and date_add(date '1998-08-21', interval 14 day)
       and page_sk = cp_catalog_page_sk
 group by cp_catalog_page_id)
 ,
 wsr as
 (select web_site_id,
        sum(sales_price) as sales,
        sum(profit) as profit,
        sum(return_amt) as returns,
        sum(net_loss) as profit_loss
 from
  ( select  ws_web_site_sk as wsr_web_site_sk,
            ws_sold_date_sk  as date_sk,
            ws_ext_sales_price as sales_price,
            ws_net_profit as profit,
            cast(0 as numeric) as return_amt,
            cast(0 as numeric) as net_loss
    from tpcds_2t_baseline.web_sales
    union all
    select ws_web_site_sk as wsr_web_site_sk,
           wr_returned_date_sk as date_sk,
           cast(0 as numeric) as sales_price,
           cast(0 as numeric) as profit,
           wr_return_amt as return_amt,
           wr_net_loss as net_loss
    from tpcds_2t_baseline.web_returns left outer join tpcds_2t_baseline.web_sales on
         ( wr_item_sk = ws_item_sk
           and wr_order_number = ws_order_number)
   ) salesreturns,
     tpcds_2t_baseline.date_dim,
     tpcds_2t_baseline.web_site
 where date_sk = d_date_sk
       and d_date between date(1998, 08, 21)
       and date_add(date '1998-08-21', interval 14 day)
       and wsr_web_site_sk = web_site_sk
 group by web_site_id)
  select  channel
        , id
        , sum(sales) as sales
        , sum(returns) as returns
        , sum(profit) as profit
 from 
 (select 'store channel' as channel
        , concat('store', s_store_id) as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from   ssr
 union all
 select 'catalog channel' as channel
        , concat('catalog_page', cp_catalog_page_id) as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from  csr
 union all
 select 'web channel' as channel
        , concat('web_site', web_site_id) as id
        , sales
        , returns
        , (profit - profit_loss) as profit
 from   wsr
 ) x
 group by rollup (channel, id)
 order by channel
         ,id
 limit 100;

-- end query 98 in stream 0 using template query5.tpl
-- start query 99 in stream 0 using template query76.tpl
select  channel, col_name, d_year, d_qoy, i_category, COUNT(*) sales_cnt, SUM(ext_sales_price) sales_amt FROM (
        SELECT 'store' as channel, 'ss_addr_sk' col_name, d_year, d_qoy, i_category, ss_ext_sales_price ext_sales_price
         FROM tpcds_2t_baseline.store_sales, tpcds_2t_baseline.item, tpcds_2t_baseline.date_dim
         WHERE ss_addr_sk IS NULL
           AND ss_sold_date_sk=d_date_sk
           AND ss_item_sk=i_item_sk
        UNION ALL
        SELECT 'web' as channel, 'ws_web_page_sk' col_name, d_year, d_qoy, i_category, ws_ext_sales_price ext_sales_price
         FROM tpcds_2t_baseline.web_sales, tpcds_2t_baseline.item, tpcds_2t_baseline.date_dim
         WHERE ws_web_page_sk IS NULL
           AND ws_sold_date_sk=d_date_sk
           AND ws_item_sk=i_item_sk
        UNION ALL
        SELECT 'catalog' as channel, 'cs_ship_mode_sk' col_name, d_year, d_qoy, i_category, cs_ext_sales_price ext_sales_price
         FROM tpcds_2t_baseline.catalog_sales, tpcds_2t_baseline.item, tpcds_2t_baseline.date_dim
         WHERE cs_ship_mode_sk IS NULL
           AND cs_sold_date_sk=d_date_sk
           AND cs_item_sk=i_item_sk) foo
GROUP BY channel, col_name, d_year, d_qoy, i_category
ORDER BY channel, col_name, d_year, d_qoy, i_category
limit 100;

 -- END OF BENCHMARK
