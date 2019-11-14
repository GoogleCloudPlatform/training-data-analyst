# BigQuery nested and repeated columns

[BQ nested and repeated columns](https://cloud.google.com/bigquery/docs/nested-repeated) 
allow you to achieve the performance benefits of denormalization while retaining the structure of the data.

To illustrate, consider [this query](https://console.cloud.google.com/bigquery?sq=316488749670:7c97c53951da457c9aaa07388f4213be) against the Bitcoin public dataset. The query joins the blocks and transactions tables to find the max transaction ID for each block.

```sql
SELECT block_id, max(i.input_sequence_number) 
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b
JOIN `bigquery-public-data.bitcoin_blockchain.transactions` AS t using(block_id), t.inputs as i 
GROUP BY block_id
```

Run the query. Under Execution details, note the slot time consumed and bytes shuffled.

Now let's run the same query using nested and repeated fields. It turns out that the bitcoin_blockchain table already includes the transactions for each block as a nested and repeated column. [This query](https://console.cloud.google.com/bigquery?sq=316488749670:7ee7c9e79a1f473db78fb1665d6b8260) gives exactly the same results, but involves only one table:

```sql
SELECT block_id, max(i.input_sequence_number) 
FROM `bigquery-public-data.bitcoin_blockchain.blocks` AS b, b.transactions AS t, t.inputs as i
GROUP BY block_id
```

Note that the total amount of data ingested is much smaller. The slot time consumed is minutes rather than hours, and there are many fewer bytes shuffled because no join was necessary. Although both queries are small and complete in about the same time, the reduction in slot time and data ingest will become increasingly noticeable with larger datasets.