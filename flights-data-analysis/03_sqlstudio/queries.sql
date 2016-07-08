use bts;
select count(dest) from flights where arr_delay <= 0 and dep_delay <= 0;
select count(dest) from flights where arr_delay > 0 and dep_delay <= 0;
select count(dest) from flights where arr_delay <= 0 and dep_delay > 0;
select count(dest) from flights where arr_delay > 0 and dep_delay > 0;
