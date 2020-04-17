import tensorflow.keras as keras

def create_cnn_model(img, params):
  ksize = params.get('ksize', 5)
  nfil = params.get('nfil', 10)
  nlayers = params.get('nlayers', 3)
  dprob = params.get('dprob', 0.05 if params['batch_norm'] else 0.25)
  cnn = keras.layers.BatchNormalization()(img)
  for layer in range(nlayers):
    nfilters = nfil * (layer + 1)  # 5, 10, 15
    cnn = keras.layers.Conv2D(nfilters, (ksize, ksize), padding='same')(cnn)
    cnn = keras.layers.Activation('elu')(cnn)
    cnn = keras.layers.BatchNormalization()(cnn)
    cnn = keras.layers.MaxPooling2D(pool_size=(2, 2))(cnn)
  cnn = keras.layers.Flatten()(cnn)
  cnn = keras.layers.Dropout(dprob)(cnn)
  cnn = keras.layers.Dense(10, activation='relu')(cnn)
  return cnn

