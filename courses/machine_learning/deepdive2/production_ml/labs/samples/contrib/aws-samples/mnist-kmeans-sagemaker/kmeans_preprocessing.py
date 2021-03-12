import pickle
import gzip
import numpy
import io
from sagemaker.amazon.common import write_numpy_to_dense_tensor

print("Extracting MNIST data set")
# Load the dataset
with gzip.open("/opt/ml/processing/input/mnist.pkl.gz", "rb") as f:
    train_set, valid_set, test_set = pickle.load(f, encoding="latin1")

# process the data
# Convert the training data into the format required by the SageMaker KMeans algorithm
print("Writing training data")
with open("/opt/ml/processing/output_train/train_data", "wb") as train_file:
    write_numpy_to_dense_tensor(train_file, train_set[0], train_set[1])

print("Writing test data")
with open("/opt/ml/processing/output_test/test_data", "wb") as test_file:
    write_numpy_to_dense_tensor(test_file, test_set[0], test_set[1])

print("Writing validation data")
# Convert the valid data into the format required by the SageMaker KMeans algorithm
numpy.savetxt(
    "/opt/ml/processing/output_valid/valid-data.csv",
    valid_set[0],
    delimiter=",",
    fmt="%g",
)
