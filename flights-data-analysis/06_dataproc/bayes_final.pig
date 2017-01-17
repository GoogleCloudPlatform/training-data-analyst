REGISTER /usr/lib/pig/piggybank.jar;

alldays = LOAD 'gs://cloud-training-demos-ml/flights/trainday.csv' 
   using org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'NO_MULTILINE', 'NOCHANGE', 'SKIP_INPUT_HEADER')
   AS (FL_DATE:chararray, is_train_day:boolean);
traindays = FILTER alldays BY is_train_day == True;

ALLFLIGHTS = 
   LOAD 'gs://cloud-training-demos-ml/flights/tzcorr/all_flights-*'
   using org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'NO_MULTILINE', 'NOCHANGE') 
   AS (FL_DATE:chararray,UNIQUE_CARRIER:chararray,AIRLINE_ID:chararray,CARRIER:chararray,FL_NUM:chararray,ORIGIN_AIRPORT_ID:chararray,ORIGIN_AIRPORT_SEQ_ID:int,ORIGIN_CITY_MARKET_ID:chararray,ORIGIN:chararray,DEST_AIRPORT_ID:chararray,DEST_AIRPORT_SEQ_ID:int,DEST_CITY_MARKET_ID:chararray,DEST:chararray,CRS_DEP_TIME:datetime,DEP_TIME:datetime,DEP_DELAY:float,TAXI_OUT:float,WHEELS_OFF:datetime,WHEELS_ON:datetime,TAXI_IN:float,CRS_ARR_TIME:datetime,ARR_TIME:datetime,ARR_DELAY:float,CANCELLED:chararray,CANCELLATION_CODE:chararray,DIVERTED:chararray,DISTANCE:float,DEP_AIRPORT_LAT:float,DEP_AIRPORT_LON:float,DEP_AIRPORT_TZOFFSET:float,ARR_AIRPORT_LAT:float,ARR_AIRPORT_LON:float,ARR_AIRPORT_TZOFFSET:float,EVENT:chararray,NOTIFY_TIME:datetime);

FLIGHTS = JOIN ALLFLIGHTS BY FL_DATE, traindays BY FL_DATE; 
FLIGHTS2 = FOREACH FLIGHTS GENERATE 
     (DISTANCE < 368? 368:
     (DISTANCE < 575? 575:
     (DISTANCE < 838? 838:
     (DISTANCE < 1218? 1218:
          9999)))) AS distbin:int,
     (DEP_DELAY < 11? 11:
     (DEP_DELAY < 12? 12:
     (DEP_DELAY < 13? 13:
     (DEP_DELAY < 14? 14:
     (DEP_DELAY < 15? 15:
     (DEP_DELAY < 16? 16:
     (DEP_DELAY < 17? 17:
     (DEP_DELAY < 18? 18:
     (DEP_DELAY < 19? 19:
          9999))))))))) AS depdelaybin:int,
     (ARR_DELAY < 15? 1:0) AS ontime:int;

grouped = GROUP FLIGHTS2 BY (distbin, depdelaybin);

probs = FOREACH grouped GENERATE 
           FLATTEN(group) AS (dist, delay), 
           ((double)SUM(FLIGHTS2.ontime))/COUNT(FLIGHTS2.ontime) AS ontime:double,
           COUNT(FLIGHTS2.ontime) AS numflights;

cancel = FILTER probs BY (numflights > 10) AND (ontime < 0.7);
bydist = GROUP cancel BY dist;
result = FOREACH bydist GENERATE group AS dist, MIN(cancel.delay) AS depdelay;

store result into 'gs://cloud-training-demos-ml/flights/pigoutput/' using PigStorage(',','-schema');
