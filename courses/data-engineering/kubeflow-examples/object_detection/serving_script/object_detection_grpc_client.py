import os

import argparse
from argparse import RawTextHelpFormatter

from grpc.beta import implementations
import numpy as np
from PIL import Image
import tensorflow as tf

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from object_detection.core.standard_fields import \
    DetectionResultFields as dt_fields

tf.logging.set_verbosity(tf.logging.INFO)

def load_image_into_numpy_array(input_image):
    image = Image.open(input_image)
    (im_width, im_height) = image.size
    image_arr = np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)
    image.close()
    return image_arr

def load_input_tensor(input_image):
    image_np = load_image_into_numpy_array(input_image)
    image_np_expanded = np.expand_dims(image_np, axis=0).astype(np.uint8)
    tensor = tf.contrib.util.make_tensor_proto(image_np_expanded)
    return tensor

def main(args):
    host, port = args.server.split(':')
    channel = implementations.insecure_channel(host, int(port))._channel
    stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
    request = predict_pb2.PredictRequest()
    request.model_spec.name = args.model_name

    input_tensor = load_input_tensor(args.input_image)
    request.inputs['inputs'].CopyFrom(input_tensor)

    result = stub.Predict(request, 60.0)
    image_np = load_image_into_numpy_array(args.input_image)

    output_dict = {}
    output_dict[dt_fields.detection_classes] = np.squeeze(
        result.outputs[dt_fields.detection_classes].float_val).astype(np.uint8)
    output_dict[dt_fields.detection_boxes] = np.reshape(
        result.outputs[dt_fields.detection_boxes].float_val, (-1, 4))
    output_dict[dt_fields.detection_scores] = np.squeeze(
        result.outputs[dt_fields.detection_scores].float_val)

    category_index = label_map_util.create_category_index_from_labelmap(args.label_map,
                                                                        use_display_name=True)

    vis_util.visualize_boxes_and_labels_on_image_array(image_np,
      output_dict[dt_fields.detection_boxes],
      output_dict[dt_fields.detection_classes],
      output_dict[dt_fields.detection_scores],
      category_index,
      instance_masks=None,
      use_normalized_coordinates=True,
      line_thickness=8)
    output_img = Image.fromarray(image_np.astype(np.uint8))
    base_filename = os.path.splitext(os.path.basename(args.input_image))[0]
    output_image_path = os.path.join(args.output_directory, base_filename + "_output.jpg")
    tf.logging.info('Saving labeled image: %s' % output_image_path)
    output_img.save(output_image_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Object detection grpc client.",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('--server',
                        type=str,
                        required=True,
                        help='PredictionService host:port')
    parser.add_argument('--model_name',
                        type=str,
                        required=True,
                        help='Name of the model')
    parser.add_argument('--input_image',
                        type=str,
                        required=True,
                        help='Path to input image')
    parser.add_argument('--output_directory',
                        type=str,
                        required=True,
                        help='Path to output directory')
    parser.add_argument('--label_map',
                        type=str,
                        required=True,
                        help='Path to label map file')

    args = parser.parse_args()
    main(args)
