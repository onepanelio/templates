"""
NNI example trial code.

- Experiment type: Hyper-parameter Optimization
- Trial framework: Tensorflow v2.x (Keras API)
- Model: LeNet-5
- Dataset: MNIST
"""

import logging
import json

import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.layers import (Conv2D, Dense, Dropout, Flatten, MaxPool2D)
from tensorflow.keras.optimizers import Adam

import nni

_logger = logging.getLogger('mnist_example')
_logger.setLevel(logging.INFO)

class ReportIntermediates(Callback):
    """
    Callback class for reporting intermediate accuracy metrics.

    This callback sends accuracy to NNI framework every 100 steps,
    so you can view the learning curve on web UI.

    If an assessor is configured in experiment's YAML file,
    it will use these metrics for early stopping.
    """
    def on_epoch_end(self, epoch, logs=None):
        """Reports intermediate accuracy to NNI framework"""
        nni.report_intermediate_result(logs['val_accuracy'])


def load_dataset():
    """Download and reformat MNIST dataset"""
    mnist = tf.keras.datasets.mnist
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0
    x_train = x_train[..., tf.newaxis]
    x_test = x_test[..., tf.newaxis]
    return (x_train, y_train), (x_test, y_test)


def save_best_metrics(loss, accuracy):
    prev_accuracy = 0

    # Get existing metrics if any
    try:
        with open('/tmp/sys-metrics.json') as f:
            prev_metrics = json.load(f)
            prev_accuracy = [m['value'] for m in prev_metrics if m['name'] == 'accuracy'][0]
    except FileNotFoundError:
        pass

    # Write metrics if new accuracy is better
    if prev_accuracy > accuracy:
        return False

    metrics = [
        {'name': 'accuracy', 'value': accuracy},
        {'name': 'loss', 'value': loss}
    ]
    with open('/tmp/sys-metrics.json', 'w') as f:
        json.dump(metrics, f)

    _logger.info('Best metrics saved')
    return True

def save_data(params, model):
    model.save('/mnt/output/model.h5')
    with open('/mnt/output/hyperparamters.json', 'w') as f:
        json.dump(params, f)
    _logger.info('Data for best trial saved')

def main(params):
    """
    Main program:
      - Prepare dataset
      - Build network
      - Train the model
      - Report accuracy to tuner
      - Save best current metrics
      - Save best current model
    """

    (x_train, y_train), (x_test, y_test) = load_dataset()
    _logger.info('Dataset loaded')
    
    model = tf.keras.Sequential([
          tf.keras.layers.Conv2D(filters=32, kernel_size=params['conv_size'], activation='relu'),
          tf.keras.layers.MaxPool2D(pool_size=2),
          tf.keras.layers.Conv2D(filters=64, kernel_size=params['conv_size'], activation='relu'),
          tf.keras.layers.MaxPool2D(pool_size=2),
          tf.keras.layers.Flatten(),
          tf.keras.layers.Dense(units=params['hidden_size'], activation='relu'),
          tf.keras.layers.Dropout(rate=params['dropout_rate']),
          tf.keras.layers.Dense(units=10, activation='softmax')
      ])
    model.compile(optimizer=tf.keras.optimizers.Adam(lr=params['learning_rate']),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    _logger.info('Model built')

    model.fit(
        x_train,
        y_train,
        batch_size=params['batch_size'],
        epochs=params['epochs'],
        callbacks=[ReportIntermediates()],
        validation_data=(x_test, y_test)
    )
    _logger.info('Training completed')

    loss, accuracy = model.evaluate(x_test, y_test, verbose=0)
    # send final accuracy to NNI tuner and web UI
    nni.report_final_result(accuracy)
    # save the best metrics so they are displayed in the Workflow Task
    is_best_accuracy = save_best_metrics(loss, accuracy)
    _logger.info('Final accuracy reported: %s', accuracy)

    # save the model if accuracy is better than previous model
    if is_best_accuracy:
        save_data(params, model)

if __name__ == '__main__':
    params = {
        'dropout_rate': 0.5,
        'conv_size': 5,
        'hidden_size': 1024,
        'batch_size': 32,
        'learning_rate': 1e-4,
        'epochs': 10,
    }

    # fetch hyper-parameters from HPO tuner
    tuned_params = nni.get_next_parameter()
    params.update(tuned_params)

    _logger.info('Hyper-parameters: %s', params)
    main(params)