/*

Demo: Querying External Data Sources from BigQuery

1. Navigate to: sheets.new (or docs.google.com/spreadsheets/ --> CREATE)

2. In the header row (Row A), enter these three headers:
Message Language Translation

3. In row B, enter these values as B1, B2, and B3 respectively:
The weather is quite nice out
es
=GOOGLETRANSLATE(A2,"en",B2)

4. Sheets just invoked the ML Translate API on your text! Change the text or copy the entire row to add another entry.

5. Ask the class what other language codes they want to translate to
Reference: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

6. Copy the URL of your spreadsheet to your clipboard

6. Open BigQuery: https://console.cloud.google.com/bigquery

7. Create a new dataset titled ecommerce (if it doesnt exist)

8. Click the dataset name, and then Create Table

9. For Source, select Drive

10. Paste in your URL

11. File format: Google Sheet

12. Dataset: Ecommerce

13. Table Name: translation

14. For Schema, edit as text and paste the below
message:STRING,
code:STRING,
translation:STRING

15. For Advanced Options > Header Rows to Skip > Put 1

16. Create Table 

17. Run the below script

*/

SELECT 
	message,
	code,
	translation
FROM ecommerce.translation

/*

18. View the results

19. Make a change to your spreadsheet (like a new message)

20. In BigQuery, run the same query again. New data!

21. Briefly mention the downsides of external data connections
- no cache for external queries
- data consistency not guaranteed (race conditions)
*/








