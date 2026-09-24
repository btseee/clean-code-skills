import numpy as np


def batches(images: np.ndarray, labels: np.ndarray, batch_size: int = 32):
    """Yield (images, labels) batches with a plain Python loop."""
    for start in range(0, len(images), batch_size):
        end = start + batch_size
        yield images[start:end], labels[start:end]
