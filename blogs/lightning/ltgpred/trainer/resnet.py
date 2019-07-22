from tensorflow import keras
import tensorflow.keras.layers as layers

LETTERS = list('abcdefghijklmnopqrstuvwxyz')
bn_axis = 3 # channels last

# based on https://github.com/keras-team/keras-applications/blob/master/keras_applications/resnet50.py
def identity_block(input_tensor, kernel_size, filters, stage, block):
  """The identity block is the block that has no conv layer at shortcut.
  # Arguments
      input_tensor: input tensor
      kernel_size: default 3, the kernel size of
          middle conv layer at main path
      filters: list of integers, the filters of 3 conv layer at main path
      stage: integer, current stage label, used for generating layer names
      block: 'a','b'..., current block label, used for generating layer names
  # Returns
      Output tensor for the block.
  """
  filters1, filters2, filters3 = filters
  conv_name_base = 'res' + str(stage) + block + '_branch'
  bn_name_base = 'bn' + str(stage) + block + '_branch'

  x = layers.Conv2D(filters1, (1, 1),
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2a')(input_tensor)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2a')(x)
  x = layers.Activation('relu')(x)

  x = layers.Conv2D(filters2, kernel_size,
                    padding='same',
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2b')(x)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2b')(x)
  x = layers.Activation('relu')(x)

  x = layers.Conv2D(filters3, (1, 1),
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2c')(x)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2c')(x)

  x = layers.add([x, input_tensor])
  x = layers.Activation('relu')(x)
  return x


def conv_block(input_tensor,
               kernel_size,
               filters,
               stage,
               block,
               strides=(2, 2)):
  """A block that has a conv layer at shortcut.
  # Arguments
      input_tensor: input tensor
      kernel_size: default 3, the kernel size of
          middle conv layer at main path
      filters: list of integers, the filters of 3 conv layer at main path
      stage: integer, current stage label, used for generating layer names
      block: 'a','b'..., current block label, used for generating layer names
      strides: Strides for the first conv layer in the block.
  # Returns
      Output tensor for the block.
  Note that from stage 3,
  the first conv layer at main path is with strides=(2, 2)
  And the shortcut should have strides=(2, 2) as well
  """
  filters1, filters2, filters3 = filters
  conv_name_base = 'res' + str(stage) + block + '_branch'
  bn_name_base = 'bn' + str(stage) + block + '_branch'

  x = layers.Conv2D(filters1, (1, 1), strides=strides,
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2a')(input_tensor)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2a')(x)
  x = layers.Activation('relu')(x)

  x = layers.Conv2D(filters2, kernel_size, padding='same',
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2b')(x)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2b')(x)
  x = layers.Activation('relu')(x)

  x = layers.Conv2D(filters3, (1, 1),
                    kernel_initializer='he_normal',
                    name=conv_name_base + '2c')(x)
  x = layers.BatchNormalization(axis=bn_axis, name=bn_name_base + '2c')(x)

  shortcut = layers.Conv2D(filters3, (1, 1), strides=strides,
                           kernel_initializer='he_normal',
                           name=conv_name_base + '1')(input_tensor)
  shortcut = layers.BatchNormalization(
    axis=bn_axis, name=bn_name_base + '1')(shortcut)

  x = layers.add([x, shortcut])
  x = layers.Activation('relu')(x)
  return x


def create_resnet_model(img_input, params):
  ksize = params.get('ksize', 5)
  nfil = params.get('nfil', 10)
  nlayers = params.get('nlayers', 3)
  dprob = params.get('dprob', 0.05 if params['batch_norm'] else 0.25)

  x = keras.layers.ZeroPadding2D(padding=(3, 3), name='conv1_pad')(img_input)
  x = keras.layers.Conv2D(nfil, (ksize, ksize),
                          strides=(2, 2),
                          padding='valid',
                          kernel_initializer='he_normal',
                          name='conv1')(x)
  bn_axis = 3  # channels_last
  x = keras.layers.BatchNormalization(axis=bn_axis, name='bn_conv1')(x)
  x = keras.layers.Activation('relu')(x)
  x = keras.layers.ZeroPadding2D(padding=(1, 1), name='pool1_pad')(x)
  x = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(x)

  # ResNet-50 has 4 of these stages
  for layer in range(nlayers):
    nfilters = nfil * (layer + 1)
    filters = [nfilters, nfilters, nfilters * 4]
    x = conv_block(x, 3, filters, stage=layer + 2, block='a', strides=(1, 1))
    for block in range(get_num_blocks(layer, nlayers)):
      x = identity_block(x, 3, filters, stage=layer + 2, block=LETTERS[block + 1])

  cnn = keras.layers.GlobalAveragePooling2D(name='avg_pool')(x)
  cnn = keras.layers.Dropout(dprob)(cnn)
  cnn = keras.layers.Dense(10, activation='relu')(cnn)
  return cnn

def get_num_blocks(layer, nlayers):
  # ResNet-50 has 2-3-5-2 for the four layers
  # if we have 5 layers, we'll end up with the following calculation
  nblocks = min(max(layer, nlayers//2),  # 0, 1, 2, 2, 2
                min(nlayers-layer-1, nlayers//2) # 2, 2, 2, 1, 0
                ) # 0, 1, 2, 1, 0
  return (nblocks + 2)  # 2-3-4-3-2


