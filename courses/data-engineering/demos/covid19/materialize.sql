#standardSQL
create or replace table covid19.us_daily_cases as
select * from covid19.daily_new_cases
	order by state, county, date
;
create or replace table covid19.us_totals as
select * from covid19.most_recent_totals
	order by state, county
