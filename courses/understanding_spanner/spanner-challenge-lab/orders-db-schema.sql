CREATE TABLE customers (
     cust_id INT64 NOT NULL, 
     cust_name STRING(MAX),
     cust_address STRING(MAX),
     cust_state STRING(MAX),
     cust_zip STRING(MAX),
     cust_email STRING(MAX),
     cust_phone STRING(MAX),

) PRIMARY KEY (cust_id);

CREATE TABLE orders (
     cust_id INT64 NOT NULL, 
     order_date DATE,
     order_num STRING(MAX) NOT NULL,
) PRIMARY KEY (order_num);

CREATE TABLE details (
     line_item_num INT64 NOT NULL, 
     order_num STRING(MAX) NOT NULL,
     prod_code INT64 NOT NULL,
     qty INT64 NOT NULL,
) PRIMARY KEY (order_num, line_item_num),
INTERLEAVE IN PARENT orders ON DELETE CASCADE;

CREATE TABLE products (
     prod_code INT64 NOT NULL, 
     prod_name STRING(MAX) NOT NULL,
     prod_desc STRING(MAX) NOT NULL,
     prod_price FLOAT64 NOT NULL,
) PRIMARY KEY (prod_code);


