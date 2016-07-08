REGISTER /usr/lib/pig/piggybank.jar;

alldays = LOAD 'gs://cloud-training-demos/flights/trainday.csv' 
   using org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'NO_MULTILINE', 'NOCHANGE', 'SKIP_INPUT_HEADER')
   AS (FL_DATE:chararray, is_train_day:boolean);
traindays = FILTER alldays BY is_train_day == True;

ALLFLIGHTS = LOAD 'gs://cloud-training-demos/flights/2015*.csv' using org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'NO_MULTILINE', 'NOCHANGE', 'SKIP_INPUT_HEADER')
AS (FL_DATE:chararray,UNIQUE_CARRIER:chararray,AIRLINE_ID:chararray,CARRIER:chararray,FL_NUM:int,ORIGIN_AIRPORT_ID:chararray,ORIGIN_SEQ_ID:chararray,ORIGIN_CITY_MARKET_ID:chararray,ORIGIN:chararray,DEST_AIRPORT_ID:chararray,DEST_AIRPORT_SEQ_ID:chararray,DEST_CITY_MARKET_ID:chararray,DEST:chararray,CRS_DEP_TIME:int,DEP_TIME:int,DEP_DELAY:float,TAXI_OUT:float,WHEELS_OFF:int,WHEELS_ON:int,TAXI_IN:float,CRS_ARR_TIME:int,ARR_TIME:int,ARR_DELAY:float,CANCELLED:float,CANCELLATION_CODE:chararray,DIVERTED:float,DISTANCE:float);

FLIGHTS = JOIN ALLFLIGHTS BY FL_DATE, traindays BY FL_DATE; 

FLIGHTS2 = FOREACH FLIGHTS GENERATE 
     (DISTANCE < 300? '<300':
       (DISTANCE < 500? '300-500':
         (DISTANCE < 800? '500-800':
           (DISTANCE < 1200? '800-1200': '> 1200')))) AS distbin:chararray,
     (DEP_DELAY < 10? 10:
       (DEP_DELAY > 29? 30: DEP_DELAY)) AS depdelaybin:float,
     (ARR_DELAY < 15? 1:0) AS ontime:int;

grouped = GROUP FLIGHTS2 BY (distbin, depdelaybin);
probs = FOREACH grouped GENERATE FLATTEN(group) AS (dist, delay), ((double)SUM(FLIGHTS2.ontime))/COUNT(FLIGHTS2.ontime) AS ontime:double, COUNT(FLIGHTS2.ontime) AS numflights;

cancel = FILTER probs BY (numflights > 10) AND (ontime < 0.7);
bydist = GROUP cancel BY dist;
result = FOREACH bydist GENERATE group AS dist, MIN(cancel.delay) AS depdelay;
store result into 'gs://cloud-training-demos/flights/pigoutput/' using PigStorage(',','-schema');
