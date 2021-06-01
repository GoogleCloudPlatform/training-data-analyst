import logging
import json
import unittest
import sys

from taxi_streaming_pipeline import *
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import BeamAssertException
from apache_beam.testing.util import assert_that, equal_to_per_window
from apache_beam.testing.test_stream import TestStream
from apache_beam.transforms.window import TimestampedValue, IntervalWindow
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

def main(out = sys.stderr, verbosity = 2):
    loader = unittest.TestLoader()
  
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(out, verbosity = verbosity).run(suite)



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

            EXPECTED_WINDOW_COUNTS = {IntervalWindow(0,60): [3],
                                      IntervalWindow(60,120): [1],
                                      IntervalWindow(120,180): [1]}

            assert_that(taxi_counts, equal_to_per_window(EXPECTED_WINDOW_COUNTS),
                        reify_windows=True)
                        
# class TaxiLateDataTest(unittest.TestCase):

#     def test_late_data_behavior(self):

#         options = PipelineOptions()
#         options.view_as(StandardOptions).streaming = True

#         with TestPipeline(options=options) as p:

#             base_json_pickup = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,\"longitude\":0.0," \
#                         "\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,\"meter_increment\":0.1," \
#                         "\"ride_status\":\"pickup\",\"passenger_count\":1}" 

#             test_stream = # TASK 3: Create TestStream Object

#             EXPECTED_RESULTS = {IntervalWindow(0,60): [2,3]}  #On Time and Late Result

#             taxi_counts = (p | test_stream
#                              | TaxiCountTransform()
#                            )

#             assert_that(taxi_counts, equal_to(EXPECTED_RESULTS))

if __name__ == '__main__':
    with open('testing.out', 'w') as f:
        main(f)