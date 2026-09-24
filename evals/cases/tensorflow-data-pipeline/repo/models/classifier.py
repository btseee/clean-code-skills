from tensorflow import keras
from tensorflow.keras import layers


class Classifier(keras.Model):
    def __init__(self) -> None:
        super().__init__()
        self.dense1 = layers.Dense(128, activation="relu")
        self.dense2 = layers.Dense(10, activation="softmax")

    def call(self, inputs):
        return self.dense2(self.dense1(inputs))
