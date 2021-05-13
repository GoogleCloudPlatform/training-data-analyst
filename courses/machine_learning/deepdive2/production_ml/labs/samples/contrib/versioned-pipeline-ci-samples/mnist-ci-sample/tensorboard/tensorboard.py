if __name__ == '__main__':
    import json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', type=str)
    parser.add_argument('--output_path', type=str, default='/mlpipeline-ui-metadata.json')

    args = parser.parse_args()

    metadata = {
      'outputs' : [{
        'type': 'tensorboard',
        'source': args.logdir,
      }]
    }
    with open(args.output_path, 'w') as f:
      json.dump(metadata, f)