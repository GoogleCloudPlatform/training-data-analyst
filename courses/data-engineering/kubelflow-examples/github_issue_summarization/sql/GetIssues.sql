SELECT
  url as issue_url
  -- replace more than one white-space character in a row with a single space
, REGEXP_REPLACE(title, r"\s{2,}", ' ') as issue_title
, REGEXP_REPLACE(body, r"\s{2,}", ' ') as body

FROM(
    SELECT
        JSON_EXTRACT(payload, '$.issue.html_url') as url
        -- extract the title and body removing parentheses, brackets, and quotes
      , LOWER(TRIM(REGEXP_REPLACE(JSON_EXTRACT(payload, '$.issue.title'), r"\\n|\(|\)|\[|\]|#|\*|`", ' '))) as title
      , LOWER(TRIM(REGEXP_REPLACE(JSON_EXTRACT(payload, '$.issue.body'), r"\\n|\(|\)|\[|\]|#|\*|`", ' '))) as body
    FROM `githubarchive.day.2017*`
    WHERE 
      -- 70 random days in 2017 (because it costs money to query these tables!!)  
          _TABLE_SUFFIX BETWEEN '0101' and '1231'
      and type="IssuesEvent" 
      -- Only want the issue at a specific point otherwise will have duplicates
      and JSON_EXTRACT(payload, '$.action') = "\"opened\"" 
) as tbl

WHERE 
  -- the body must be at least 8 words long and the title at least 3 words long
  --  this is an arbitrary way to filter out empty or sparse issues
      ARRAY_LENGTH(SPLIT(body, ' ')) >= 6
  and ARRAY_LENGTH(SPLIT(title, ' ')) >= 3
  -- filter out issues that have really long titles or bodies
  --    (these are outliers, and will slow tokenization down).
  and LENGTH(title) <= 400
  and LENGTH(body) <= 2000
