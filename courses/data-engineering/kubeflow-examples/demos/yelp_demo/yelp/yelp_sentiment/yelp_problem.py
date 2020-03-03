import csv
import os
import zipfile

from tensor2tensor.data_generators import generator_utils, imdb, problem
from tensor2tensor.models import transformer
from tensor2tensor.utils import registry


@registry.register_problem
class YelpSentiment(imdb.SentimentIMDB):

  # Use the below file to generate the full dataset of 17,746,271 records.
  #YELP_DATASET_URL = "https://storage.googleapis.com/kubeflow-examples/datasets/yelp-dataset.zip"
  YELP_DATASET_URL = \
    "https://storage.googleapis.com/kubeflow-examples/datasets/yelp_review_1000000.zip"

  @property
  def is_generate_per_split(self):
    return False

  @property
  def dataset_splits(self):
    return [{
      "split": problem.DatasetSplit.TRAIN,
      "shards": 9,
    }, {
      "split": problem.DatasetSplit.EVAL,
      "shards": 1,
    }]

  @property
  def vocab_filename(self):
    return "sentiment_yelp.vocab.%d" % self.approx_vocab_size

  @property
  def num_classes(self):
    return 2

  @property
  def approx_vocab_size(self):
    return 40000

  @staticmethod
  def class_labels(data_dir):
    del data_dir
    return ["pos", "neg"]

  def generate_samples(self, data_dir, tmp_dir, dataset_split): #pylint: disable=unused-argument
    compressed_filename = os.path.basename(self.YELP_DATASET_URL)
    generator_utils.maybe_download(tmp_dir, compressed_filename, self.YELP_DATASET_URL)
    zip_ref = zipfile.ZipFile(os.path.join(tmp_dir, compressed_filename), 'r')
    zip_ref.extractall(tmp_dir)
    zip_ref.close()

    with open(os.path.join(tmp_dir, 'yelp_review.csv'), 'r') as csvfile:
      yelp_data = csv.reader(csvfile)
      header_row = True
      for row in yelp_data:
        # Skip first row
        if header_row:
          header_row = False
          continue
        rating = int(row[3]) # rating : 1 - 5
        label = None
        # pos for 4,5 neg for 1,2
        if rating == 3:
          continue
        elif rating > 3:
          label = 1
        else:
          label = 0
        yield {
          "inputs": row[5],
          "label": label,
        }


@registry.register_hparams
def transformer_yelp_sentiment():
  # https://github.com/tensorflow/tensor2tensor/blob/99750c4b6858de46b75b067e3a967fe74da1c874/tensor2tensor/models/transformer.py#L1040
  hparams = transformer.transformer_base_single_gpu()
  return hparams
