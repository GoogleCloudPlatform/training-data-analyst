#standardSQL
CREATE VIEW IF NOT EXISTS covid19.daily_new_cases AS
SELECT state, county, date,
first_value(cases) OVER recent as tot_cases,
cases - lead(cases) OVER recent as new_cases, cases,
deaths - lead(deaths) OVER recent as new_deaths, deaths
FROM covid19.us_counties
WINDOW recent AS (PARTITION BY state, county ORDER BY date DESC)
ORDER BY state, county, date DESC
;
CREATE VIEW IF NOT EXISTS covid19.most_recent_totals AS
WITH most_recent AS (
SELECT state, county, date,
row_number() OVER latest as rownum,
cases - lead(cases) OVER latest as new_cases, 
deaths - lead(deaths) OVER latest as new_deaths,
cases as tot_cases,
deaths as tot_deaths
FROM covid19.us_counties
WINDOW latest AS (PARTITION BY state, county ORDER BY date DESC )
)
SELECT state, county, date, new_cases, tot_cases, new_deaths, tot_deaths
FROM most_recent
WHERE rownum = 1
