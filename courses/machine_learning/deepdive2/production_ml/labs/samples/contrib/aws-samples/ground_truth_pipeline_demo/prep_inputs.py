# Source: https://github.com/awslabs/amazon-sagemaker-examples/blob/master/ground_truth_labeling_jobs/from_unlabeled_data_to_deployed_machine_
#         learning_model_ground_truth_demo_image_classification/from_unlabeled_data_to_deployed_machine_learning_model_ground_truth_demo_image_
#         classification.ipynb

import itertools
import json
import numpy as np
import boto3

BUCKET = "<your-bucket-name>"
EXP_NAME = "mini-image-classification/ground-truth-demo"

# Make sure the bucket is in the same region as this notebook.
region = boto3.session.Session().region_name
s3 = boto3.client("s3")
bucket_region = s3.head_bucket(Bucket=BUCKET)["ResponseMetadata"]["HTTPHeaders"][
    "x-amz-bucket-region"
]
assert (
    bucket_region == region
), "You S3 bucket {} and this notebook need to be in the same region.".format(BUCKET)

# Process the Open Images annotations.
with open("openimgs-annotations.csv", "r") as f:
    all_labels = [line.strip().split(",") for line in f.readlines()]

# Extract image ids in each of our desired classes.
ims = {}
ims["Musical Instrument"] = [
    label[0] for label in all_labels if (label[2] == "/m/04szw" and label[3] == "1")
][:500]
ims["Fruit"] = [
    label[0] for label in all_labels if (label[2] == "/m/02xwb" and label[3] == "1")
][:371]
ims["Fruit"].remove(
    "02a54f6864478101"
)  # This image contains personal information, let's remove it from our dataset.
num_classes = len(ims)

# If running the short version of the demo, reduce each class count 50 times.
for key in ims.keys():
    ims[key] = set(ims[key][: int(len(ims[key]) / 50)])

# Copy the images to our local bucket.
print("Copying images to bucket")
s3 = boto3.client("s3")
for img_id, img in enumerate(itertools.chain.from_iterable(ims.values())):
    copy_source = {"Bucket": "open-images-dataset", "Key": "test/{}.jpg".format(img)}
    s3.copy(copy_source, BUCKET, "{}/images/{}.jpg".format(EXP_NAME, img))

# Create and upload the input manifests.
input_data_paths = [
    "s3://{}/{}/images/{}.jpg".format(BUCKET, EXP_NAME, img)
    for img in itertools.chain.from_iterable(ims.values())
]

# Shuffle input paths in place.
np.random.shuffle(input_data_paths)

dataset_size = len(input_data_paths)
train_test_split_index = round(dataset_size * 0.8)

print("Number of training samples: " + str(train_test_split_index))
print("Number of validation samples: " + str(dataset_size - train_test_split_index))

train_data_paths = input_data_paths[:train_test_split_index]
validation_data_paths = input_data_paths[train_test_split_index:]

with open("train.manifest", "w") as f:
    for img_path in train_data_paths:
        f.write('{"source-ref": "' + img_path + '"}\n')

with open("validation.manifest", "w") as f:
    for img_path in validation_data_paths:
        f.write('{"source-ref": "' + img_path + '"}\n')

s3.upload_file("train.manifest", BUCKET, EXP_NAME + "/" + "train.manifest")
s3.upload_file("validation.manifest", BUCKET, EXP_NAME + "/" + "validation.manifest")
print("Uploaded manifests at s3://{}/{}".format(BUCKET, EXP_NAME))

# Specify categories
CLASS_LIST = list(ims.keys())
print("Label space is {}".format(CLASS_LIST))

json_body = {"labels": [{"label": label} for label in CLASS_LIST]}
with open("class_labels.json", "w") as f:
    json.dump(json_body, f)

s3.upload_file("class_labels.json", BUCKET, EXP_NAME + "/class_labels.json")

# Create UI template
img_examples = [
    "https://s3.amazonaws.com/open-images-dataset/test/{}".format(img_id)
    for img_id in ["0634825fc1dcc96b.jpg", "0415b6a36f3381ed.jpg"]
]


def make_template(test_template=False, save_fname="instructions.template"):
    template = r"""<script src="https://assets.crowd.aws/crowd-html-elements.js"></script>
    <crowd-form>
      <crowd-image-classifier
        name="crowd-image-classifier"
        src="{{{{ task.input.taskObject | grant_read_access }}}}"
        header="Dear Annotator, please tell me what you can see in the image. Thank you!"
        categories="{categories_str}"
      >
        <full-instructions header="Image classification instructions">
        </full-instructions>

        <short-instructions>
          <p>Dear Annotator, please tell me whether what you can see in the image. Thank you!</p>
          <p><img src="{}" style="max-width:100%">
          <br>Example "Musical Instrument". </p>

          <p><img src="{}" style="max-width:100%">
          <br>Example "Fruit".</p>

        </short-instructions>

      </crowd-image-classifier>
    </crowd-form>""".format(
        *img_examples,
        categories_str=str(CLASS_LIST)
        if test_template
        else "{{ task.input.labels | to_json | escape }}"
    )

    with open(save_fname, "w") as f:
        f.write(template)


make_template(test_template=True, save_fname="instructions.html")
make_template(test_template=False, save_fname="instructions.template")
s3.upload_file("instructions.template", BUCKET, EXP_NAME + "/instructions.template")
