import json
import typing
import logging
import apache_beam as beam

class WeatherRecord(typing.NamedTuple):
    loc_id: str
    lat: float
    lng: float
    date: str
    low_temp: float
    high_temp: float
    precip: float

beam.coders.registry.register_coder(WeatherRecord, beam.coders.RowCoder)

class ConvertCsvToWeatherRecord(beam.DoFn):

    def process(self, line):
        fields = 'loc_id,lat,lng,date,low_temp,high_temp,precip'.split(',')
        values = line.split(',')
        row = dict(zip(fields,values))
        for num_field in ('lat', 'lng', 'low_temp', 'high_temp', 'precip'):
            row[num_field] = float(row[num_field])
        yield WeatherRecord(**row)

class ConvertTempUnits(beam.DoFn):

    def process(self, row):
        row_dict = row._asdict()
        for field in ('low_temp', 'high_temp'):
            row_dict[field] = row_dict[field] * 1.8 + 31.0
        yield WeatherRecord(**row_dict)

class ConvertToJson(beam.DoFn):

    def process(self, row):
        line = json.dumps(row._asdict())
        yield line

class ComputeStatistics(beam.PTransform):

    def expand(self, pcoll):
    
        results = (
            pcoll | 'ComputeStatistics' >> beam.GroupBy('loc_id')
                                                .aggregate_field('low_temp', min, 'record_low')
                                                .aggregate_field('high_temp', max, 'record_high')
                                                .aggregate_field('precip', sum, 'total_precip')
                | 'ToJson' >> beam.ParDo(ConvertToJson())
        )
        
        return results

class WeatherStats(beam.PTransform):

    def expand(self, pcoll):

        results = (
            pcoll | "ParseCSV" >> beam.ParDo(ConvertCsvToWeatherRecord())
                  | "ConvertToF" >> beam.ParDo(ConvertTempUnits())
                  | "ComputeStats" >> ComputeStatistics()
        )

        return results

def run():

    p = beam.Pipeline()

    (p | 'ReadCSV' >> beam.io.ReadFromText('./weather_data.csv')
       | 'ComputeStatistics' >> WeatherStats()
       | 'WriteJson' >> beam.io.WriteToText('./weather_stats', '.json')
    )

    logging.getLogger().setLevel(logging.INFO)
    logging.info("Building pipeline ...")

    p.run()

if __name__ == '__main__':
  run()
