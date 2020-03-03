import logging
import nmslib


class CodeSearchEngine:
  """Instantiate the Search Index instance.

  This is a utility class which takes an nmslib
  index file and a data file to return data from.

  Args:
    index_file: Path string to the nmslib index file.
    lookup_data: A list representing the data in the same order as in index.
    embedding_fn: A function which takes a string and returns a high-dimensional
                  embedding.
  """

  DICT_LABELS = ['nwo', 'path', 'function_name', 'lineno', 'original_function']

  def __init__(self, index_file, lookup_data, embedding_fn):
    self.index = CodeSearchEngine.nmslib_init()
    self.index.loadIndex(index_file)

    self.lookup_data = lookup_data
    self.embedding_fn = embedding_fn

  def query(self, query_str, k=2):
    logging.info("Embedding query: %s", query_str)
    embedding = self.embedding_fn(query_str)
    logging.info("Calling knn server")
    idxs, dists = self.index.knnQuery(embedding, k=k)

    result = [dict(zip(self.DICT_LABELS, self.lookup_data[id])) for id in idxs]
    for i, dist in enumerate(dists):
      result[i]['score'] = str(dist)
    return result

  @staticmethod
  def nmslib_init():
    """Initializes an nmslib index object."""
    index = nmslib.init(method='hnsw', space='cosinesimil')
    return index

  @staticmethod
  def create_index(data, save_path):
    """Add numpy data to the index and save to path."""
    index = CodeSearchEngine.nmslib_init()
    index.addDataPointBatch(data)
    index.createIndex({'post': 2}, print_progress=True)
    index.saveIndex(save_path)
