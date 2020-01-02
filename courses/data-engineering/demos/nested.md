# Querying a Bitcoin dataset in BigQuery with nested and repeated columns

[BQ nested and repeated columns](https://cloud.google.com/bigquery/docs/nested-repeated) 
allow you to achieve the performance benefits of denormalization while retaining the structure of the data.

To illustrate, consider [this query](https://console.cloud.google.com/bigquery?sq=316488749670:7c97c53951da457c9aaa07388f4213be) against the Bitcoin public dataset. The query joins the blocks and transactions tables to find the max transaction ID for each block.

```sql
SELECT 
  block_id, 
  MAX(i.input_sequence_number) AS max_seq_number,
  COUNT(t.transaction_id) as num_transactions_in_block
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b
  -- Join on the separate table which stores transaction info
  JOIN `bigquery-public-data.bitcoin_blockchain.transactions` AS t USING(block_id)
  , t.inputs as i 
GROUP BY block_id;
```

Run the query. Under Execution details, note the slot time consumed and bytes shuffled.

Now let's run the same query using nested and repeated fields. It turns out that the bitcoin_blockchain table already includes the transactions for each block as a nested and repeated column. This query gives exactly the same results, but involves only one table:

```sql
SELECT 
  block_id, 
  MAX(i.input_sequence_number) AS max_seq_number,
  COUNT(t.transaction_id) as num_transactions_in_block
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b
  -- Use the nested STRUCT within BLOCKS table for transactions instead of a separate JOIN
  , b.transactions AS t
  , t.inputs as i
GROUP BY block_id;
```

Note that the total amount of data ingested is much smaller. The slot time consumed is minutes rather than hours, and there are many fewer bytes shuffled because no join was necessary. Although both queries are small and complete in about the same time, the reduction in slot time and data ingest will become increasingly noticeable with larger datasets.


## Querying repeated columns (arrays) in a table with UNNEST()

Each transaction as part of a block also shows how many Bitcoins are being sent as the output. 
Let's find the transaction in our dataset that has the highest amount of Bitcoin sent. 

The smallest unit of a Bitcoin transaction is a `satoshi` which is 0.00000001 BTC. Let's try summing
`transactions.outputs.output_satoshis` which is a repeated field of integer values representing the total
value of that transaction's output. 

Does the simple SUM query below work? Why or why not?

### Fix the query: Top 10 Bitcoin blocks by BTC transaction value

```sql
SELECT DISTINCT
  block_id, 
  TIMESTAMP_MILLIS(timestamp) AS timestamp,
  t.transaction_id,
  t.outputs.output_satoshis AS satoshi_value,
  t.outputs.output_satoshis * 0.00000001 AS btc_value
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b
  , b.transactions AS t 
  , t.inputs as i
ORDER BY btc_value DESC
LIMIT 10;
```

You should get this error. 

`Error: Cannot access field output_satoshis on a value with type ARRAY<STRUCT<output_satoshis INT64, output_script_bytes BYTES, output_script_string STRING, ...>> at [5:13]`

__What happened?__
The `output_satoshis` field is an array and we need to unpack it first before analyzing it or else we'll have data at differing levels of granularity. 


Solution: Use UNNEST() When you need to break apart ARRAY values for analysis. 
Here the transactions.outputs.output_satoshis field is an array that needs to be unnested before we can analyze it:

```sql
SELECT DISTINCT
  block_id, 
  TIMESTAMP_MILLIS(timestamp) AS timestamp,
  t.transaction_id,
  t_outputs.output_satoshis AS satoshi_value,
  t_outputs.output_satoshis * 0.00000001 AS btc_value
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b
  , b.transactions AS t 
  , t.inputs as i
  , UNNEST(t.outputs) AS t_outputs
ORDER BY btc_value DESC
LIMIT 10;
```

Tip: Be extra cautious when giving aliases to your tables and structs. Try to make them clear for the reader like `t_outputs` clearly comes from the `transactions` struct and the child `outputs` struct within. 

## Additional analysis

Recall that a single block in the chain can have many confirmed transactions. Let's lookup the actual block that our large transaction was a part of:

```sql
SELECT * 
FROM `bigquery-public-data.bitcoin_blockchain.blocks` 
WHERE block_id = '00000000000000fb62bbadc0a9dcda556925b2d0c1ad8634253ac2e83ab8382f'
```

Scroll through the block and see all the repeated transaction values that are a part of the block. Confirm the previous 50,000 BTC transaction is there.

Tip: If you're analyzing this dataset in the future, be sure to filter `transactions.outputs.output_pubkey_base58` WHERE IS NOT NULL to ensure the BTC transaction did not error. 
