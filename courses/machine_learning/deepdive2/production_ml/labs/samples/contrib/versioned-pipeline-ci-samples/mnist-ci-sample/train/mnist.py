def mnisttrain(storage_bucket:str):
    import tensorflow as tf
    import json
    mnist = tf.keras.datasets.mnist
    (x_train,y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train/255.0, x_test/255.0

    def create_model():
        return tf.keras.models.Sequential([
            tf.keras.layers.Flatten(input_shape = (28,28)),
            tf.keras.layers.Dense(512, activation = 'relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(10, activation = 'softmax')
        ])
    model = create_model()
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    import datetime
    import os
    log_dir = os.path.join(storage_bucket, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

    model.fit(x=x_train, 
              y=y_train, 
              epochs=5, 
              validation_data=(x_test, y_test), 
              callbacks=[tensorboard_callback])

    print('At least tensorboard callbacks are correct')
    with open('/logdir.txt', 'w') as f:
      f.write(log_dir)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--storage_bucket', type=str)

    args = parser.parse_args()
    mnisttrain(args.storage_bucket)