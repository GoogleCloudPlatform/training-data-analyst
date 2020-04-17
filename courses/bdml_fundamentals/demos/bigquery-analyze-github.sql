# Demo adapted from https://medium.com/@hoffa/400-000-github-repositories-1-billion-files-14-terabytes-of-code-spaces-or-tabs-7cfe0b5dd7fd

# Optional: Uncomment to Explore data tables below or run entire query as-is for tabs vs spaces demo (takes 20 seconds to run)
-- SELECT *
-- FROM `fh-bigquery.github_extracts.contents_top_repos_top_langs`
-- WHERE sample_repo_name = 'GoogleCloudPlatform/training-data-analyst'
-- # Output: Real lines of code from our training repo on Github 
-- # note: above demo extract last updated 2016 
-- # for full github tables for students to explore later see: https://medium.com/google-cloud/github-on-bigquery-analyze-all-the-code-b3576fd2b150

-- SELECT
--   SUM(copies) AS total_files, # 1b
--   SUM(copies*size) AS total_size_in_bytes # 14 TB of code
-- FROM `fh-bigquery.github_extracts.contents_top_repos_top_langs`
-- # Output: 1 Billion files, 14 TB of Github code to analyze


# Demo: Practice your SQL to parse every line of 133 GB of GitHub code
# to see by programming language whether tabs or spaces are used more

# break out individual lines of code into new lines
WITH lines_of_code AS (
SELECT 
  SPLIT(content, '\n') AS line, # split out individual lines of code into array
  sample_path, 
  sample_repo_name 
FROM `fh-bigquery.github_extracts.contents_top_repos_top_langs`
)

# each line of code is now part of an array
# SELECT * FROM lines_of_code LIMIT 100;

# let's flatten the array to we can parse it more easily
, flattened_lines_of_code AS (
SELECT 
  flattened_line,
  sample_path,
  sample_repo_name
FROM lines_of_code, UNNEST(line) AS flattened_line
)

# flattened array (note each path and repo_name repeats now) 
# SELECT * FROM flattened_lines_of_code LIMIT 100;


# parse the first character from every line of code
, parse_first_character AS (
SELECT 
  SUBSTR(flattened_line,1,1) AS first_character,
  flattened_line,
  sample_path,
  sample_repo_name
FROM flattened_lines_of_code
)

# filter for code lines that begin with tab or space only
, tabs_or_spaces AS(
SELECT
  first_character,
  IF(REGEXP_CONTAINS(first_character, r'[\t]'),1,0) AS tab_count,
  IF(REGEXP_CONTAINS(first_character, r'[ ]'),1,0) AS space_count,
  flattened_line,
  sample_path,
  sample_repo_name
FROM parse_first_character
WHERE REGEXP_CONTAINS(first_character, r'[ \t]') # only look at tabs or spaces
)

# aggregate and filter by entire code file 
, tabs_or_spaces_count AS (
SELECT 
  COUNT(flattened_line) AS lines,
  SUM(tab_count) AS tabs_count,
  SUM(space_count) AS spaces_count,
  IF(SUM(tab_count) > SUM(space_count), 1,0) AS tab_winner,
  IF(SUM(tab_count) < SUM(space_count), 1,0) AS space_winner,
  REGEXP_EXTRACT(sample_path, r'\.([^\.]*)$') AS extension,
  sample_path,
  sample_repo_name
FROM tabs_or_spaces
GROUP BY sample_path, sample_repo_name
HAVING tabs_count > 10 OR spaces_count > 10 # only include files with more than 10 instances
)

# aggregate all files by code extension (.java etc.)
, tabs_or_spaces_by_extension AS ( 
SELECT 
  extension,
  COUNT(lines) AS files,
  SUM(lines) AS lines,
  SUM(tab_winner) AS tabs,
  SUM(space_winner) AS spaces,
  LOG((SUM(space_winner)+1)/(SUM(tab_winner)+1)) lratio
FROM tabs_or_spaces_count
GROUP BY extension
ORDER BY files DESC
LIMIT 100 # only include top 100 by extension volume
)

SELECT
  extension,
  # FORMAT() for demo readability on screen, don't use otherwise. Leave that for Data Studio
  FORMAT("%'d", files) AS files,
  FORMAT("%'d", lines) AS lines,
  FORMAT("%'d", tabs) AS tabs,
  FORMAT("%'d", spaces) AS spaces,
  ROUND(lratio,5) AS lratio
FROM tabs_or_spaces_by_extension
# 16s to process 133GB of GitHub code

# Discussion of results:
# winner is SPACES in most cases except for C programming language

# interesting insight: GO lang uses tabs 
# see: https://stackoverflow.com/questions/19094704/indentation-in-go-tabs-or-spaces

# BigQuery discussion:
# after query is ran, select Execution details to compare Elapsed time (20s) vs Slot time consumed (30+ minutes)
# Ask: We know we only waited about 20 seconds for the results. What's this 30+ minute number mean then?

# Inside of the BigQuery service are lots of virtual machines that massively process 
# your data and query logic in parallel. These workers or "slots" work together to process a single query job
# really quickly. For accounts with on-demand pricing, you can have up to 2,000 slots

# So say we had 30 minutes of slot time or 1800 seconds. If the query took 20 seconds in total to run, 
# but it was 1800 seconds worth of work, how many workers at minimum worked on it? 1800/20 = 90
# And that's assuming each worker instantly had all the data it needed and was at full capacity for all 20 seconds
# In reality, workers have a variety of tasks (waiting for data, reading it, performing computations, and writing data)
# and also need to compare notes with eachother on what work was already done on the job. The good news for you is
# that you don't need to worry about optimizing these workers or the underlying data to run perfectly in parallel. That's
# why BigQuery is a managed service -- there's an entire team dedicated to hardware and data storage optimization.

# In case you were wondering, the worker limit for your project is 2,000 slots at once. As a general rule, 
# if you're processing less than 100 GB of queries all at once, you're unlikely to be using all 2,000 slots.

# If you're really interested in BigQuery performance (say you have a team of 100 analysts and want to monitor usage)
# you can monitor usage with StackDriver: https://app.google.stackdriver.com/services/bigquery?project=bdml-demos

# We can now see we used about 50-100 slots for the previous query. 

# Appendix: Setup your own monitoring
# Slot quota monitoring: https://cloud.google.com/bigquery/quotas#queries
# and https://cloud.google.com/bigquery/docs/monitoring