# JavaProjectsThatNeedHelp revisited (optional ELT demo)

The Data Engineering course Dataflow side inputs lab queries 2 million rows in BQ which runs parallel pipeline branches and merges them back together to compute a composite score for each Java package in popular open source projects.

It turns out that the Java code can be rewritten as a Javascript UDF (user-defined 
function) in BigQuery. In addition, some of the parsing can be cleverly rewritten as a SQL UDF for improved performance. The following SQL code, courtesy of [Stephan Meyn](https://github.com/smeyn), achieves the exact same results, but much faster. In addition, the getPackages() method courtesy of Alex Lamana uses a SQL UDF with UNNEST to emit one row for each level of the package name.
* Dataflow python: ~13 min
* Dataflow Java: ~10 min
* BigQuery: 10 sec

This is a fun way to point out to students the advantage of doing as much transformation as possible in BigQuery itself (the ELT paradigm in Data Engineering 2.x). The 60x speedup is due to at least a couple factors:
* The data itself remains in BQ's highly performance storage subsystem. BQ workers can read from native storage faster than Dataflow workers can read over the network (unless perhaps you were to use a larger Dataflow instance type, but even then I suspect the BQ workers are topographically closer to BQ native storage).
* Unlike Dataflow workers, BQ workers incur no VM startup overhead and there are more of them (up to 2000 per project by default).

Here is the high-performance query:

```sql
#StandardSQL
# take a package and break it into subpackages
# e.g.
# com.google.package.subpackage is turned into an array of:
# com
# com.google
# com.google.package
# com.google.package.subpackage
CREATE TEMP FUNCTION getPackages(input STRING, delimiter STRING) AS (
  (SELECT ARRAY_AGG(prefix)
   FROM (
    SELECT ARRAY_TO_STRING(
      ARRAY_AGG(value) OVER(ORDER BY i ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
      delimiter) prefix
    FROM UNNEST(SPLIT(input, delimiter)) value WITH OFFSET i
    )
  )
);
# Extract the package statements, all import statenments and FIXME/TODO statements
with baseImport as (
  SELECT REGEXP_EXTRACT(content, "\\s*package (.+);") as package ,
  REGEXP_EXTRACT_ALL(content, "\\s*import (.+);") as importedpackage
  ,REGEXP_EXTRACT_ALL(content, "FIXME|TODO") as needhelp
  FROM `fh-bigquery.github_extracts.contents_java_2016` ),
  
# for needhelp organise the packages and the nr of help needed stmts  
packagesWithHelp as (
  select getPackages(package, ".") as packageList, 
  array_length(needhelp) as numHelp
  from BaseImport where package is not null),

# flatten into multiple records, one per package, and aggregate over package  
needsHelp as (
   select flattenedPackage as package, sum(numhelp) as numhelp
   from packagesWithHelp
   CROSS JOIN UNNEST(packagesWithHelp.packageList) as flattenedPackage
   group by package),

# get all imports, split them up as well and flatten the imported packages   
Imports as (
  SELECT package, getPackages(flattenedImports, ".")  as importedpackages
  from BaseImport
  CROSS JOIN UNNEST(BaseImport.importedpackage) as flattenedImports),

# flatten the imported packages as well and count how many times a package is imported  
package_use as (
  SELECT imported, count(*) as numtimesUsed
  from imports
  CROSS JOIN UNNEST(imports.importedpackages) as imported
  group by imported
),

# join imported stats with help needed stats and calculate a score
final as (   
  select 
    package_use.imported as package, 
    package_use.numTimesUsed,
     numhelp, 
     needsHelp.package as nPackage,
     LOG(package_use.numTimesUsed) * log(numhelp) as score
  from package_use 
  join  needsHelp on needsHelp.package = package_use.imported
  and numhelp > 0)
  
select * from final 
order by score desc
```
