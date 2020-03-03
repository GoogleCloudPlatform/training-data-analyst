import csv
import io
import apache_beam as beam


class DictToCSVString(beam.DoFn):
  """Convert incoming dict to a CSV string.

  This DoFn converts a Python dict into
  a CSV string.

  Args:
    fieldnames: A list of strings representing keys of a dict.
  """
  def __init__(self, fieldnames):
    super(DictToCSVString, self).__init__()

    self.fieldnames = fieldnames

  def process(self, element, *_args, **_kwargs):
    """Convert a Python dict instance into CSV string.

    This routine uses the Python CSV DictReader to
    robustly convert an input dict to a comma-separated
    CSV string. This also handles appropriate escaping of
    characters like the delimiter ",". The dict values
    must be serializable into a string.

    Args:
      element: A dict mapping string keys to string values.
        {
          "key1": "STRING",
          "key2": "STRING"
        }

    Yields:
      A string representing the row in CSV format.
    """
    fieldnames = self.fieldnames
    filtered_element = {
      key: value.encode('utf-8')
      for (key, value) in element.iteritems()
      if key in fieldnames
    }
    with io.BytesIO() as stream:
      writer = csv.DictWriter(stream, fieldnames)
      writer.writerow(filtered_element)
      csv_string = stream.getvalue().strip('\r\n')

    yield csv_string
