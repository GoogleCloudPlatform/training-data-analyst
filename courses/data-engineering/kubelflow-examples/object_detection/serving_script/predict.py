""" Script to send prediction request.

Usage:
  python predict.py --url=YOUR_KF_HOST/models/coco --input_image=YOUR_LOCAL_IMAGE
    --output_image=OUTPUT_IMAGE_NAME.

This will save the prediction result as OUTPUT_IMAGE_NAME.
The output image is the input image with the detected bounding boxes.
"""
import argparse
import json
import requests
import numpy as np
from PIL import Image

import visualization_utils as vis_util

WIDTH = 1024
HEIGHT = 768

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--url", help='The url to send the request')
  parser.add_argument("--input_image", default='image1.jpg')
  parser.add_argument("--output_image", default='output.jpg')
  args = parser.parse_args()

  img = Image.open(args.input_image)
  img = img.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
  img_np = np.array(img)

  res = requests.post(
    args.url,
    data=json.dumps({"instances": [{"inputs": img_np.tolist()}]}))
  if res.status_code != 200:
    print('Failed: {}'.format(res.text))
    return

  output_dict = json.loads(res.text).get('predictions')[0]

  vis_util.visualize_boxes_and_labels_on_image_array(
    img_np,
    np.array(output_dict['detection_boxes']),
    map(int, output_dict['detection_classes']),
    output_dict['detection_scores'],
    {},
    instance_masks=output_dict.get('detection_masks'),
    use_normalized_coordinates=True,
    line_thickness=8)

  output_image = Image.fromarray(img_np)
  output_image.save(args.output_image)

if __name__ == '__main__':
  main()
