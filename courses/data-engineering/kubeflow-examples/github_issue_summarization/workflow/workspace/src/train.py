import argparse
import numpy as np
from keras.callbacks import CSVLogger, ModelCheckpoint
from keras.layers import Input, GRU, Dense, Embedding, BatchNormalization
from keras.models import Model
from keras import optimizers
from seq2seq_utils import load_decoder_inputs, load_encoder_inputs, load_text_processor

# Parsing flags.
parser = argparse.ArgumentParser()
parser.add_argument("--input_body_preprocessor_dpkl")
parser.add_argument("--input_title_preprocessor_dpkl")
parser.add_argument("--input_train_title_vecs_npy")
parser.add_argument("--input_train_body_vecs_npy")
parser.add_argument("--output_model_h5")
parser.add_argument("--learning_rate", default="0.001")
args = parser.parse_args()
print(args)

learning_rate = float(args.learning_rate)

encoder_input_data, doc_length = load_encoder_inputs(args.input_train_body_vecs_npy)
decoder_input_data, decoder_target_data = load_decoder_inputs(args.input_train_title_vecs_npy)

num_encoder_tokens, body_pp = load_text_processor(args.input_body_preprocessor_dpkl)
num_decoder_tokens, title_pp = load_text_processor(args.input_title_preprocessor_dpkl)

# Arbitrarly set latent dimension for embedding and hidden units
latent_dim = 300

###############
# Encoder Model.
###############
encoder_inputs = Input(shape=(doc_length,), name='Encoder-Input')

# Word embeding for encoder (ex: Issue Body)
x = Embedding(num_encoder_tokens,
              latent_dim,
              name='Body-Word-Embedding',
              mask_zero=False)(encoder_inputs)
x = BatchNormalization(name='Encoder-Batchnorm-1')(x)

# We do not need the `encoder_output` just the hidden state.
_, state_h = GRU(latent_dim, return_state=True, name='Encoder-Last-GRU')(x)

# Encapsulate the encoder as a separate entity so we can just
# encode without decoding if we want to.
encoder_model = Model(inputs=encoder_inputs, outputs=state_h, name='Encoder-Model')

seq2seq_encoder_out = encoder_model(encoder_inputs)

################
# Decoder Model.
################
decoder_inputs = Input(shape=(None,), name='Decoder-Input')  # for teacher forcing

# Word Embedding For Decoder (ex: Issue Titles)
dec_emb = Embedding(num_decoder_tokens,
                    latent_dim,
                    name='Decoder-Word-Embedding',
                    mask_zero=False)(decoder_inputs)
dec_bn = BatchNormalization(name='Decoder-Batchnorm-1')(dec_emb)

# Set up the decoder, using `decoder_state_input` as initial state.
decoder_gru = GRU(latent_dim, return_state=True, return_sequences=True, name='Decoder-GRU')
decoder_gru_output, _ = decoder_gru(dec_bn, initial_state=seq2seq_encoder_out)
x = BatchNormalization(name='Decoder-Batchnorm-2')(decoder_gru_output)

# Dense layer for prediction
decoder_dense = Dense(num_decoder_tokens, activation='softmax', name='Final-Output-Dense')
decoder_outputs = decoder_dense(x)

################
# Seq2Seq Model.
################

seq2seq_Model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

seq2seq_Model.compile(optimizer=optimizers.Nadam(lr=learning_rate),
                      loss='sparse_categorical_crossentropy')

seq2seq_Model.summary()

script_name_base = 'tutorial_seq2seq'
csv_logger = CSVLogger('{:}.log'.format(script_name_base))
model_checkpoint = ModelCheckpoint(
    '{:}.epoch{{epoch:02d}}-val{{val_loss:.5f}}.hdf5'.format(script_name_base), save_best_only=True)

batch_size = 1200
epochs = 7
history = seq2seq_Model.fit([encoder_input_data, decoder_input_data],
                            np.expand_dims(decoder_target_data, -1),
                            batch_size=batch_size,
                            epochs=epochs,
                            validation_split=0.12,
                            callbacks=[csv_logger, model_checkpoint])

#############
# Save model.
#############
seq2seq_Model.save(args.output_model_h5)
