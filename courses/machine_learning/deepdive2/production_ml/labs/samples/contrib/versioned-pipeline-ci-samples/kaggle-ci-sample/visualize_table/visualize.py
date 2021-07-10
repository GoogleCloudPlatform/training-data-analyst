def datatable(
    train_file_path
):
    import pandas as pd
    import json
    train_file = pd.read_csv(train_file_path)
    header = train_file.columns.tolist()
    metadata = {
        'outputs' : [{
            'type': 'table',
            'storage': 'gcs',
            'format': 'csv',
            'header': header,
            'source': train_file_path
            }]
        }
    with open('/mlpipeline-ui-metadata.json', 'w') as f:
        json.dump(metadata, f)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_file_path', type = str)
    args = parser.parse_args()

    datatable(args.train_file_path)
