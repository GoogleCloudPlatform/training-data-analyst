# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import argparse
import numpy as np
from keras.datasets import cifar10


def main():
    parser = argparse.ArgumentParser(description='Data processor')
    parser.add_argument('--input_dir', help='Raw data directory')
    parser.add_argument('--output_dir', help='Processed data directory')

    args = parser.parse_args()

    def load_and_process_data(input_dir):
        processed_data = cifar10.load_data()
        return processed_data

    def save_data(processed_data, output_dir):
        (x_train, y_train), (x_test, y_test) = processed_data
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        np.save(os.path.join(output_dir, 'x_train.npy'), x_train)
        np.save(os.path.join(output_dir, 'y_train.npy'), y_train)
        np.save(os.path.join(output_dir, 'x_test.npy'), x_test)
        np.save(os.path.join(output_dir, 'y_test.npy'), y_test)

    processed_data = load_and_process_data(args.input_dir)
    save_data(processed_data, args.output_dir)

    with open('/output.txt', 'w') as f:
        f.write(args.output_dir)

    print('input_dir: {}'.format(args.input_dir))
    print('output_dir: {}'.format(args.output_dir))


if __name__ == "__main__":
    main()
