# TensorFlow

> Applies to: TensorFlow 2.16+ with Keras 3 (multi-backend: JAX, TensorFlow, PyTorch; current stable 2.21). Language pack: languages/python.md. Read with: nothing.

## Structure

- `data/` — `tf.data.Dataset` pipelines: loading, parsing, shuffling, augmentation, batching, prefetching.
- `models/` — `keras.Model` or `keras.layers.Layer` subclasses and functional/Sequential graphs; no training loop.
- `training/` — the training loop or `model.fit()` call, optimizer, callbacks, checkpointing.
- `configs/` — hyperparameters, paths, and split ratios, out of code (G35).
- `checkpoints/` or `artifacts/` — saved `.keras` files; gitignored, never hand-edited.
- A notebook, where the project has one, only calls into these; it owns no logic of its own.

## Roles

```clean-roles
role data = **/data/**, **/datasets/**
role training = **/training/**
role config = **/configs/**
signal model = \(\s*(?:keras\.|layers\.)?(?:Model|Layer)\b
allow data = model
```

## Rules

- Import `keras` directly (Keras 3, the default since TensorFlow 2.16), not `tensorflow.keras`, unless the project deliberately pins legacy `tf_keras` (G24).
- Never write a Python `for`/`while` loop feeding examples or batches to the model; build a `tf.data.Dataset` and express the pipeline with `map`, `batch`, `shuffle`, and `prefetch(tf.data.AUTOTUNE)` (G6).

```python
dataset = (
    tf.data.Dataset.from_tensor_slices((images, labels))
    .shuffle(1000)
    .map(augment, num_parallel_calls=tf.data.AUTOTUNE)
    .batch(32)
    .prefetch(tf.data.AUTOTUNE)
)
```

- Wrap a hot custom training step in `@tf.function`; do not leave per-step Python-level dispatch untraced in production training code.
- Fit augmentation, normalization, and encoding into the `tf.data` pipeline or a preprocessing layer, never into the training loop or a notebook cell (G17).
- Set determinism explicitly before training — `keras.utils.set_random_seed(seed)` plus `tf.config.experimental.enable_op_determinism()` — never seed with legacy `np.random.seed` alone (NPY002).
- Build train/val/test `Dataset`s from disjoint sources; never shuffle once and slice the same buffer per run, which leaks examples across splits (G3).
- Save with `model.save("name.keras")` (or `keras.saving.save_model`) as the source of truth for reloading; use `model.export(path)` only for serving.
- Push hyperparameters, paths, and split ratios into `configs/`; never hard-code a learning rate or file path inside a model or training module (G35).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Model architecture is policy: a `models/` module never imports `tf.data`, file paths, or a config loader.
- `data/` and `training/` are infrastructure and orchestration: they call the model; the model never calls them.
- Declare a `typing.Protocol` for a data source a training loop depends on (a batch iterator), and implement it in `data/`.
- Compose datasets, model, optimizer, and callbacks in `training/`'s entry point, not scattered across modules.

```clean-architecture
layer domain      = **/models/**
layer application = **/training/**
layer adapters    = **/data/**, **/datasets/**
layer main        = **/train.py, **/main.py
```

## Tests

- Use `tf.test.TestCase` (or plain pytest) for numeric assertions — `assertAllClose`, `assertShapeEqual` — with an explicit tolerance.
- Assert output shape and dtype for every model and layer; a shape test catches a broadcasting bug before a training run does (T5).
- Overfit one small batch to near-zero loss as a training-loop smoke test; a loop that cannot memorize ten examples has a bug, not a hard problem.
- Test the `tf.data` pipeline apart from the model: assert a known input produces the expected augmented shape and range.
- Seed every test that touches randomness; a flaky shape or loss test hides a real regression (F.I.R.S.T.).

## Enforce

- Ruff `NPY` rules (`NPY002` legacy `np.random` calls) plus the complexity and unused-argument rules from the Python pack.
- mypy or pyright on `data/` and `models/`; a pipeline's `map` function is the easiest place to leave a shape or dtype wrong.
- pytest-randomly to surface a test that only passes for one seed; reproduce a failure with the seed it reports, never rerun until green (G4, T7).
- import-linter for the layers contract above, where declared.

## Smells

- A Python loop feeding NumPy batches into the model by hand instead of a `tf.data.Dataset` (G6).
- Augmentation or normalization written inline in the training loop instead of the pipeline (G17).
- A notebook cell holding logic no module owns, replayable only in one cell order (G31).
- Train/validation overlap from shuffling once and slicing, instead of a disjoint split built into the pipeline (G3).
- A hard-coded learning rate, path, or batch size buried in a model or training function (G35, G25).
- Mixing `tensorflow.keras` and standalone `keras` imports in the same module (G11).
