"""
step #4: submit result to kaggle
"""

def download_result(
    result_file
):
    import gcsfs
    fs = gcsfs.GCSFileSystem()
    fs.get(result_file, 'submission.csv')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--result_file', type=str)
    parser.add_argument('--submit_message', type=str, default = 'default submit')
    args = parser.parse_args()

    download_result(args.result_file)
    import os
    os.system("kaggle competitions submit -c house-prices-advanced-regression-techniques -f submission.csv -m " + args.submit_message)

    