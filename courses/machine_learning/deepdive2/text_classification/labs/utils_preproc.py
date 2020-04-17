"""Utilities for preprocessing natural language for machine learning"""
import re
import unicodedata

import tensorflow as tf


def unicode_to_ascii(s):
    """Transforms an ascii string into unicode."""
    normalized = unicodedata.normalize('NFD', s)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def preprocess_sentence(w):
    """Lowers, strips, and adds <start> and <end> tags to a sentence.
    """
    w = unicode_to_ascii(w.lower().strip())

    # creating a space between a word and the punctuation following it
    # eg: "he is a boy." => "he is a boy ."
    w = re.sub(r"([?.!,¿])", r" \1 ", w)

    w = re.sub(r'[" "]+', " ", w)

    # replacing everything with space except (a-z, A-Z, ".", "?", "!", ",")
    w = re.sub(r"[^a-zA-Z?.!,¿]+", " ", w)

    w = w.rstrip().strip()

    # adding a start and an end token to the sentence
    # so that the model know when to start and stop predicting.
    w = '<start> ' + w + ' <end>'
    return w


def tokenize(lang, lang_tokenizer=None):
    """Given a list of sentences, return an integer representation

    Arguments:
    lang -- a python list of sentences
    lang_tokenizer -- keras_preprocessing.text.Tokenizer, if None
        this will be created for you

    Returns:
    tensor -- int tensor of shape (NUM_EXAMPLES,MAX_SENTENCE_LENGTH)
    lang_tokenizer -- keras_preprocessing.text.Tokenizer
    """
    if lang_tokenizer is None:
        lang_tokenizer = tf.keras.preprocessing.text.Tokenizer(
          filters='')
        lang_tokenizer.fit_on_texts(lang)

    tensor = lang_tokenizer.texts_to_sequences(lang)

    tensor = tf.keras.preprocessing.sequence.pad_sequences(
        tensor, padding='post')

    return tensor, lang_tokenizer


def preprocess(sentences, tokenizer):
    """Preprocesses then tokenizes text

    Arguments:
    sentences -- a python list of of strings
    tokenizer -- Tokenizer for mapping words to integers

    Returns:
    tensor -- int tensor of shape (NUM_EXAMPLES,MAX_SENTENCE_LENGTH)
    lang_tokenizer -- keras_preprocessing.text.Tokenizer
    """
    sentences = [preprocess_sentence(sentence) for sentence in sentences]
    tokens, _ = tokenize(sentences, tokenizer)
    return tokens


def int2word(tokenizer, int_sequence):
    """Converts integer representation to natural language representation

    Arguments:
    tokenizer -- keras_preprocessing.text.Tokenizer
    int_sequence -- an iterable or rank 1 tensor of integers

    Returns list of string tokens
    """
    return [tokenizer.index_word[t] if t != 0 else '' for t in int_sequence]
