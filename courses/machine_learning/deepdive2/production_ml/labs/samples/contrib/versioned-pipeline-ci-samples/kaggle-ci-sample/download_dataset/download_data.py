"""
step #1: download data from kaggle website, and push it to gs bucket
"""

def process_and_upload(
    bucket_name
):
    from google.cloud import storage
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name.lstrip('gs://'))
    train_blob = bucket.blob('train.csv')
    test_blob = bucket.blob('test.csv')
    train_blob.upload_from_filename('train.csv')
    test_blob.upload_from_filename('test.csv')

    with open('train.txt', 'w') as f:
        f.write(bucket_name+'/train.csv')
    with open('test.txt', 'w') as f:
        f.write(bucket_name+'/test.csv')

if __name__ == '__main__':
    import os
    os.system("kaggle competitions download -c house-prices-advanced-regression-techniques")
    os.system("unzip house-prices-advanced-regression-techniques")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', type=str)
    args = parser.parse_args()

    process_and_upload(args.bucket_name)
    