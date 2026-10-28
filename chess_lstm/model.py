def require_tensorflow():
    try:
        import tensorflow as tf
    except ImportError as error:
        raise RuntimeError(
            "TensorFlow is required for chess LSTM training and loading. "
            "Install the dependencies from requirements-chess-lstm.txt."
        ) from error
    return tf


def create_model(
    vocabulary_size,
    sequence_length,
    embedding_dim=64,
    lstm_units=128,
    mask_zero=False,
):
    tf = require_tensorflow()
    inputs = tf.keras.Input(shape=(sequence_length,), dtype="int32")
    embedded = tf.keras.layers.Embedding(
        vocabulary_size, embedding_dim, mask_zero=mask_zero
    )(inputs)
    encoded = tf.keras.layers.LSTM(lstm_units)(embedded)
    outputs = tf.keras.layers.Dense(vocabulary_size, activation="softmax")(encoded)
    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def load_model(path):
    return require_tensorflow().keras.models.load_model(path)
