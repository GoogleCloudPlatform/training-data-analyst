import logging
import json
import unittest

from taxi_streaming_pipeline import *
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import BeamAssertException
from apache_beam.testing.util import assert_that, equal_to
from apache_beam.testing.test_stream import TestStream
from apache_beam.transforms.window import TimestampedValue
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


class TaxiWindowingTest(unittest.TestCase):

    def test_windowing_behavior(self):

        options = PipelineOptions()
        options.view_as(StandardOptions).streaming = True

        with TestPipeline(options=options) as p:

            base_json_pickup = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,\"longitude\":0.0," \
                         "\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,\"meter_increment\":0.1," \
                         "\"ride_status\":\"pickup\",\"passenger_count\":1}" 

            base_json_enroute = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,\"longitude\":0.0," \
                         "\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,\"meter_increment\":0.1," \
                         "\"ride_status\":\"pickup\",\"passenger_count\":1}" 
            

            test_stream = TestStream().advance_watermark_to(0).add_elements([
                TimestampedValue(base_json_pickup, 0),
                TimestampedValue(base_json_pickup, 0),
                TimestampedValue(base_json_enroute, 0),
                TimestampedValue(base_json_pickup, 60)
            ]).advance_watermark_to(60).advance_processing_time(60).add_elements([
                TimestampedValue(base_json_pickup, 120)
            ]).advance_watermark_to_infinity()

            taxi_counts = (p | test_stream
                             | TaxiCountTransform()
                          )

            EXPECTED_COUNTS = [{'taxi_rides': 3, 'timestamp': '1970-01-01T00:00:00'},
                               {'taxi_rides': 1, 'timestamp': '1970-01-01T00:01:00'}, 
                               {'taxi_rides': 1, 'timestamp': '1970-01-01T00:02:00'}]

            assert_that(taxi_counts, equal_to(EXPECTED_COUNTS))

class TaxiLateDataTest(unittest.TestCase):

        def test_late_data_behavior(self):

            options = PipelineOptions()
            options.view_as(StandardOptions).streaming = True

            with TestPipeline(options=options) as p:

                base_json_pickup = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,\"longitude\":0.0," \
                            "\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,\"meter_increment\":0.1," \
                            "\"ride_status\":\"pickup\",\"passenger_count\":1}" 

                test_stream = TestStream().advance_watermark_to(0).add_elements([
                    TimestampedValue(base_json_pickup, 0),
                    TimestampedValue(base_json_pickup, 0),
                ]).advance_watermark_to(60).advance_processing_time(60).add_elements([
                    TimestampedValue(base_json_pickup, 0)
                ]).advance_watermark_to(300).advance_processing_time(240).add_elements([
                    TimestampedValue(base_json_pickup, 0)
                ])

                EXPECTED_RESULTS = [{'taxi_rides': 2, 'timestamp': '1970-01-01T00:00:00'}, ## On Time
                                    {'taxi_rides': 3, 'timestamp': '1970-01-01T00:00:00'}] ## Late trigger

                taxi_counts = (p | test_stream
                             | TaxiCountTransform()
                          )


                assert_that(taxi_counts, equal_to(EXPECTED_RESULTS))
