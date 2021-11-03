create database if not exists bts;
use bts;

drop table if exists flights;

create table flights (
  FL_DATE date,
  UNIQUE_CARRIER varchar(16),
  AIRLINE_ID varchar(16),
  CARRIER varchar(16),
  FL_NUM integer,
  ORIGIN_AIRPORT_ID varchar(16),
  ORIGIN_SEQ_ID varchar(16),
  ORIGIN_CITY_MARKET_ID varchar(16),
  ORIGIN varchar(16),
  DEST_AIRPORT_ID varchar(16),
  DEST_AIRPORT_SEQ_ID varchar(16),
  DEST_CITY_MARKET_ID varchar(16),
  DEST varchar(16),
  CRS_DEP_TIME integer,
  DEP_TIME integer,
  DEP_DELAY float,
  TAXI_OUT float,
  WHEELS_OFF integer,
  WHEELS_ON integer,
  TAXI_IN float,
  CRS_ARR_TIME integer,
  ARR_TIME integer,
  ARR_DELAY float,
  CANCELLED float,
  CANCELLATION_CODE varchar(16),
  DIVERTED float,
  DISTANCE float,
  INDEX (FL_DATE), INDEX (ORIGIN_AIRPORT_ID), INDEX(ARR_DELAY), INDEX(DEP_TIME), INDEX(DEP_DELAY)
);

