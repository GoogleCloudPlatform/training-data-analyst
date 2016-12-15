use bts;
CREATE VIEW delayed_10 AS SELECT * FROM flights WHERE dep_delay > 10;
CREATE VIEW delayed_15 AS SELECT * FROM flights WHERE dep_delay > 15;
CREATE VIEW delayed_20 AS SELECT * FROM flights WHERE dep_delay > 20;

