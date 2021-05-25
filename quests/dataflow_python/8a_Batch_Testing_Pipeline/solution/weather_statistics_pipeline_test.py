import logging
import json
import unittest
import sys

from weather_statistics_pipeline import *
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import BeamAssertException
from apache_beam.testing.util import assert_that, equal_to

def main(out = sys.stderr, verbosity = 2):
    loader = unittest.TestLoader()
  
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(out, verbosity = verbosity).run(suite)


class ConvertToWeatherRecordTest(unittest.TestCase):

    def test_convert_to_csv(self):

        with TestPipeline() as p:

            LINES = ['x,0.0,0.0,2/2/2021,1.0,2.0,0.1']
            EXPECTED_OUTPUT = [WeatherRecord('x', 0.0, 0.0, '2/2/2021', 1.0, 2.0, 0.1)]

            input_lines = p | beam.Create(LINES)

            output = input_lines | beam.ParDo(ConvertCsvToWeatherRecord())

            assert_that(output, equal_to(EXPECTED_OUTPUT))

class ConvertTempUnitsTest(unittest.TestCase):

    def test_convert_temp_units(self):

        with TestPipeline() as p:

            RECORDS = [WeatherRecord('x', 0.0, 0.0, '2/2/2021', 1.0, 2.0, 0.1),
                       WeatherRecord('y', 0.0, 0.0, '2/2/2021', -3.0, -1.0, 0.3)]

            EXPECTED_RECORDS = [WeatherRecord('x', 0.0, 0.0, '2/2/2021', 33.8, 35.6, 0.1),
                               WeatherRecord('y', 0.0, 0.0, '2/2/2021', 26.6, 30.2, 0.3)]

            input_records = p | beam.Create(RECORDS)

            output = input_records | beam.ParDo(ConvertTempUnits())
            
            assert_that(output, equal_to(EXPECTED_RECORDS))

class ComputeStatsTest(unittest.TestCase):
    
    def test_compute_statistics(self):

        with TestPipeline() as p:

            INPUT_RECORDS = [WeatherRecord('x', 0.0, 0.0, '2/2/2021', 33.8, 35.6, 0.1),
                             WeatherRecord('x', 0.0, 0.0, '2/3/2021', 41.6, 65.3, 0.2),
                             WeatherRecord('x', 0.0, 0.0, '2/4/2021', 45.3, 52.6, 0.2),
                             WeatherRecord('y', 0.0, 0.0, '2/2/2021', 12.8, 23.6, 0.1),
                             WeatherRecord('y', 0.0, 0.0, '2/3/2021', 26.6, 30.2, 0.3)]

            EXPECTED_STATS = [json.dumps({'loc_id': 'x', 'record_low': 33.8, 'record_high': 65.3, 'total_precip': 0.5 }),
                              json.dumps({'loc_id': 'y', 'record_low': 12.8, 'record_high': 30.2, 'total_precip': 0.4 })]

            inputs = p | beam.Create(INPUT_RECORDS)

            output = inputs | ComputeStatistics()

            assert_that(output, equal_to(EXPECTED_STATS))

class WeatherStatsTransformTest(unittest.TestCase):

    def test_weather_stats_transform(self):

        with TestPipeline() as p:

            INPUT_STRINGS = ["x,31.4,-39.2,2/2/21,4.0,7.5,0.1",
                             "x,31.4,-39.2,2/2/21,3.5,6.0,0.3",
                             "y,33.4,-49.2,2/2/21,12.5,17.5,0.5"]

            EXPECTED_STATS = [json.dumps({'loc_id': 'x', 'record_low': 38.3, 'record_high': 45.5, 'total_precip': 0.4 }),
                              json.dumps({'loc_id': 'y', 'record_low': 54.5, 'record_high': 63.5, 'total_precip': 0.5 })]

            inputs = p | beam.Create(INPUT_STRINGS)

            output = inputs | WeatherStats()

            assert_that(output, equal_to(EXPECTED_STATS))
            
if __name__ == '__main__':
    with open('testing.out', 'w') as f:
        main(f)