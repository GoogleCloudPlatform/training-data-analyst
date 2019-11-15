# Querying External Data Sources from BigQuery

An external data source (also known as a federated data source) is a data source that you can query directly even though the data is not stored in BigQuery. Instead of loading or streaming the data, you create a table that references the external data source.

## Currently supported external data sources
- Cloud Storage (CSV, Orc, Parquet, Avro, JSON, etc..)
- Cloud SQL (mySQL, SQL Server, PostGres)
- Google Drive (Google Sheets)
- BigTable 

Refer to the [documentation](https://cloud.google.com/bigquery/external-data-sources) for a complete list.

## Challenge: Querying data directly from Google Sheets

1. Navigate to: [sheets.new](sheets.new) (or [docs.google.com/spreadsheets/](docs.google.com/spreadsheets/) --> CREATE)

2. Paste in the below table at the very top of the sheet (cell A1)

| Message     | Language    | Translation |
| ----------- | ----------- | ----------- |
| The weather is quite nice out | es | =GOOGLETRANSLATE(A2,"en",B2)

3. In row B, enter these values as B1, B2, and B3 respectively:

4. Sheets just invoked the ML Translate API on your text! Change the text or copy the entire row to add another entry.

5. Pick other [language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) you want to translate to

6. Copy the URL of your spreadsheet to your clipboard

7. Open BigQuery: https://console.cloud.google.com/bigquery

8. Create a new dataset titled ecommerce (if it doesnt exist)

9. Click the dataset name, and then Create Table

10. For Source, select Drive

11. Paste in your URL

12. File format: Google Sheet

13. Dataset: Ecommerce

14. Table Name: translation

15. For Schema, edit as text and paste the below

```
message:STRING,
code:STRING,
translation:STRING
```

16. For Advanced Options > Header Rows to Skip > Put 1

17. Create Table 

18. Run the below script

```sql
SELECT 
  message,
  code,
  translation
FROM ecommerce.translation
```

19. View the results

20. Make a change to your spreadsheet (like a new message)

21. In BigQuery, run the same query again. New data!

Note: Downsides of external data connections
- no cache for external queries
- data consistency not guaranteed (race conditions)








