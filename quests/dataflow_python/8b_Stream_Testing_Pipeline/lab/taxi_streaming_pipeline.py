import json
import typing
import logging
import apache_beam as beam
from apache_beam.transforms.trigger import AccumulationMode, AfterCount, AfterWatermark
from apache_beam.transforms.combiners import CountCombineFn
import argparse

class TaxiRide(typing.NamedTuple):
    ride_id: str
    point_idx: int
    latitude: float
    longitude: float
    timestamp: str
    meter_reading: float
    meter_increment: float
    ride_status: str
    passenger_count: int

beam.coders.registry.register_coder(TaxiRide, beam.coders.RowCoder)

class JsonToTaxiRide(beam.DoFn):

    def process(self, line):
        row = json.loads(line)
        yield TaxiRide(**row)

class ConvertCountToDict(beam.DoFn):

    def process(self, element, window=beam.DoFn.WindowParam):
        window_start = window.start.to_utc_datetime().strftime("%Y-%m-%dT%H:%M:%S")
        output = {"taxi_rides" : element, "timestamp": window_start}
        yield output


class TaxiCountTransform(beam.PTransform):

    def expand(self, pcoll):
        
        output = (pcoll
                    | "ParseJson" >> beam.ParDo(JsonToTaxiRide())
                    | "FilterForPickups" >> beam.Filter(lambda x : x.ride_status == 'pickup')
                    | "WindowByMinute" >> beam.WindowInto(beam.window.FixedWindows(60),
                                              trigger=AfterWatermark(late=AfterCount(1)),
                                              allowed_lateness=60,
                                              accumulation_mode=AccumulationMode.ACCUMULATING)
                    | "CountPerMinute" >> beam.CombineGlobally(CountCombineFn()).without_defaults()
                 )

        return output

def run():

    parser = argparse.ArgumentParser(description='Load from Json from Pub/Sub into BigQuery')

    parser.add_argument('--table_name', required=True, help='Output BQ table')

    opts = parser.parse_args()

    table_name = opts['table_name']

    table_schema = {
        "fields": [
            {
                "name": "taxi_rides",
                "type": "INTEGER"
            },
            {
                "name": "timestamp",
                "type": "STRING"
            },

        ]
    }

    p = beam.Pipeline()

    (p | "ReadFromPubSub" >> beam.io.ReadFromPubSub(topic="projects/pubsub-public-data/topics/taxirides-realtime") 
       | "TaxiPickupCount" >> TaxiCountTransform()
       | "ConvertToDict" >> beam.ParDo(ConvertCountToDict())
       | 'WriteAggToBQ' >> beam.io.WriteToBigQuery(
                table_name,
                schema=table_schema,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
                )
    )

if __name__ == '__main__':

    run()