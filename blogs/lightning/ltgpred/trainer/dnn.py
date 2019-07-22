import tensorflow.keras as keras

def create_dnn_model(img, params):
  nfil = params.get('nfil', 5)
  dprob = params.get('dprob', 0.05 if params['batch_norm'] else 0.25)
  nlayers = params.get('nlayers', 3)
  x = keras.layers.BatchNormalization()(img)
  for layer in range(nlayers):
    numnodes = (nlayers - layer) * nfil # 15, 10, 5 for example
    x = keras.layers.Dense(numnodes, activation='relu')(x)
  x = keras.layers.Flatten()(x)
  x = keras.layers.Dropout(dprob)(x)
  x = keras.layers.Dense(10, activation='relu')(x)
  return x
