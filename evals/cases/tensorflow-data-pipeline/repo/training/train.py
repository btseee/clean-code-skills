from data.loader import batches
from models.classifier import Classifier


def train(images, labels, epochs: int = 3):
    model = Classifier()
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")

    for epoch in range(epochs):
        for batch_images, batch_labels in batches(images, labels):
            model.train_on_batch(batch_images, batch_labels)
        print(f"epoch {epoch} done")

    return model
