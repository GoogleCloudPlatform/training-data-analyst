import tensorflow as tf
import unittest

from . import util
from . import model

BENCHMARK_ERROR = .12
BENCHMARK_ACCURACY = 1 - BENCHMARK_ERROR
BATCH_SIZE = 100

# Add or remove types below ['linear', 'dnn', 'dnn_dropout', 'cnn'].
MODEL_TYPES = ['linear', 'dnn', 'dnn_dropout', 'cnn']
EPOCHS = 10
STEPS = 100


class TestInputFunction(unittest.TestCase):
    def create_shape_test(self, training):
        mnist = tf.keras.datasets.mnist.load_data()
        dataset = util.load_dataset(mnist, training, batch_size=BATCH_SIZE)
        data_iter = dataset.__iter__()
        (images, labels) = data_iter.get_next()
        expected_image_shape = (BATCH_SIZE, model.HEIGHT, model.WIDTH, 1)
        expected_label_ndim = 2
        self.assertEqual(images.shape, expected_image_shape)
        self.assertEqual(labels.numpy().ndim, expected_label_ndim)

    def test_train_dataset_batches_has_correct_shapes(self):
        self.create_shape_test(True)

    def test_eval_dataset_batches_has_correct_shapes(self):
        self.create_shape_test(False)


class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.histories = {}

        for model_type in MODEL_TYPES:
            print('\n*** Building model for', model_type, '***\n')
            layers = model.get_layers(model_type)
            image_model = model.build_model(layers, None)
            history = model.train_and_evaluate(
                image_model, EPOCHS, STEPS, None)
            cls.histories[model_type] = history.history

    def test_beats_benchmark(self):
        for model_type in MODEL_TYPES:
            with self.subTest(model_type=model_type):
                result = self.histories[model_type]
                self.assertGreater(result['accuracy'][-1], BENCHMARK_ACCURACY)
                self.assertGreater(
                    result['val_accuracy'][-1], BENCHMARK_ACCURACY)

    def test_accuracy_is_improving(self):
        for model_type in MODEL_TYPES:
            with self.subTest(model_type=model_type):
                history = self.histories[model_type]
                accuracy = history['accuracy']
                val_accuracy = history['val_accuracy']
                self.assertLess(accuracy[0], accuracy[1])
                self.assertLess(accuracy[1], accuracy[-1])
                self.assertLess(val_accuracy[0], val_accuracy[1])
                self.assertLess(val_accuracy[1], val_accuracy[-1])

    def test_loss_is_decreasing(self):
        for model_type in MODEL_TYPES:
            with self.subTest(model_type=model_type):
                history = self.histories[model_type]
                loss = history['loss']
                val_loss = history['val_loss']
                self.assertGreater(loss[0], loss[1])
                self.assertGreater(loss[1], loss[-1])
                self.assertGreater(val_loss[0], val_loss[1])
                self.assertGreater(val_loss[1], val_loss[-1])


if __name__ == '__main__':
    unittest.main()
