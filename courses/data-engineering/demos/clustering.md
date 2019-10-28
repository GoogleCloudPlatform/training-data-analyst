# BigQuery clustering

[BQ clustering](https://cloud.google.com/bigquery/docs/clustered-tables) 
can dramatically reduce the time and cost of queries on large datasets.

The [Wikipedia pageviews](https://console.cloud.google.com/bigquery?sq=316488749670:97c8ffb43aad44a98a5ff80e1375c62b) query runs over a dataset which is partitioned but not clustered:

```sql
#https://medium.com/google-cloud/bigquery-optimized-cluster-your-tables-65e2f684594b
SELECT title, sum(views) AS sumViews
#Change to v3 for clustered table
FROM `fh-bigquery.wikipedia_v2.pageviews_2018`
WHERE datehour >= "2018-01-01"
AND wiki IN ("en","en.m")
AND regexp_contains(title, "G.*o.*o.*g.*")
GROUP BY title
ORDER BY sumViews DESC
```

To show the benefit of partitioning, change the date to "2018-07-01" and note the reduction in bytes ingested. Run the query. Expand the Execution details tab and note:
* total bytes processed (which should match the validator's number in green) * elapsed time
* slot time
* bytes shuffled
* number of rows ingested in the first stage of the query

Now modify the query to use a clustered version of the dataset by changing the dataset name from "v2" to "v3". Note the ~50% reduction in all the above metrics. BQ can take advantage of clustering even for queries involving LIKE and regular expressions as long as the first letter is fixed. Note that the total bytes processed is less than the validator's number because the validator does not yet take into account clustering, but the user is only billed for the amount actually processed.

We can infer that BQ uses a fairly large block size for clustering. In this case, it's still having to ingest about half the blocks (~1TB), suggesting that titles beginning with A-L may be clustered together, or perhaps A-G and G-L. In this example, the benefit from clustering is therefore not as great as it would be in a larger dataset. It is possible for a query over a clustered petabyte dataset to result in ingest of only a few hundred GB.