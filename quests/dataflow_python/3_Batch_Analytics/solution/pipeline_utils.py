import typing
import json
from datetime import datetime
import apache_beam as beam

class CommonLog(typing.NamedTuple):
    ip: str
    user_id: str
    lat: float
    lng: float
    timestamp: str
    http_request: str
    http_response: int
    num_bytes: int
    user_agent: str

beam.coders.registry.register_coder(CommonLog, beam.coders.RowCoder)

def parse_json(element):
    row = json.loads(element)
    return CommonLog(**row)

def add_timestamp(element: CommonLog):
    event_time = datetime.strptime(element.timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    ts = event_time.timestamp()
    return beam.window.TimestampedValue(element, ts)

class GetTimestampFn(beam.DoFn):
    def process(self, element: int, window=beam.DoFn.WindowParam):
        window_start_str = window.start.to_rfc3339()
        output = {'page_views': element, 'timestamp': window_start_str}
        yield output