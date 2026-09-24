# PyTorch

> Applies to: PyTorch 2.x (current stable 2.14), with `torch.compile`. Language pack: languages/python.md. Read with: nothing.

## Structure

- `data/` — `Dataset` subclasses and `DataLoader` construction; transforms live here, not in the training loop.
- `models/` — `nn.Module` subclasses (or `LightningModule`, where the project uses Lightning); construction only, no training loop.
- `training/` — the training loop, optimizer, scheduler, checkpointing (or a `Trainer` call, under Lightning).
- `configs/` — hyperparameters, paths, and device/precision settings, out of code (G35).
- `checkpoints/` — saved `state_dict`s; gitignored, never hand-edited.
- An entry script (`train.py`, `main.py`) resolves the device, builds data, model, and optimizer, then calls in; it holds no rules.

## Roles

```clean-roles
role data = **/data/**, **/datasets/**
role training = **/training/**
role config = **/configs/**
signal model = \(\s*(?:pl\.|pytorch_lightning\.|lightning\.pytorch\.)?LightningModule\b
signal model = \(\s*(?:nn\.)?Module\b
signal data = \(\s*(?:torch\.utils\.data\.)?Dataset\b
allow data = model
```

## Rules

- Resolve one `device` at the entry point and pass it in; never hard-code `.cuda()` or `.to("cuda")` inside a model, dataset, or training function (G35).

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = Net().to(device)
inputs, labels = inputs.to(device), labels.to(device)
```

- Call `model.train()` before a training pass and `model.eval()` before evaluation or inference; a dropout or batch-norm layer behaves wrong under the other mode (G3).
- Name a model or layer for what it computes (`ResidualBlock`), never `Net2` or `model_final`.
- Wrap evaluation and inference in `torch.inference_mode()` (preferred) or `torch.no_grad()`; neither sets eval mode, so pair it with `model.eval()` (G4).
- Seed every source of randomness together — `torch.manual_seed`, and each `DataLoader` worker via `worker_init_fn`/`generator` — and call `torch.use_deterministic_algorithms(True)` where reproducibility outweighs speed.
- Set `DataLoader`'s `num_workers`, `pin_memory`, and `persistent_workers` for the target hardware; do not leave `num_workers=0` by default on a multi-core machine (G35).
- Save `model.state_dict()` (and the optimizer's) for checkpoints; never `torch.save(model)` the pickled object, which breaks across refactors and code moves.
- Note a tensor's expected shape at a function boundary — a shape comment (`# (batch, channels, height, width)`) or a `jaxtyping`/`torchtyping` annotation where the project uses one (G19).
- Push hyperparameters, paths, and device/precision settings into `configs/`; never hard-code them in a model or training module (G35).
- Under Lightning, keep `training_step`/`validation_step` free of data-loading and metric-plumbing boilerplate a `DataModule` or logger provides; never hand-roll a loop the `Trainer` already runs (G5).
- Compile a hot training or inference path with `torch.compile(model)`; profile before reaching for `mode="reduce-overhead"` or `"max-autotune"` (G32).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Model architecture is policy: a `models/` module never imports `Dataset`/`DataLoader`, file paths, or a config loader.
- `data/` and `training/` are infrastructure and orchestration: call the model; the model never calls them.
- Declare a `typing.Protocol` for a data source a training loop depends on (a batch iterator), and implement it in `data/`.
- Compose the device, datasets, model, optimizer, and scheduler in the entry point, not scattered across modules.

```clean-architecture
layer domain      = **/models/**
layer application = **/training/**
layer adapters    = **/data/**, **/datasets/**
layer main        = **/train.py, **/main.py
```

## Tests

- Assert output shape and dtype for every model and custom layer against a fixed input (T5).
- Overfit one batch to near-zero loss as a training-loop smoke test; a loop that cannot memorize ten examples has a bug, not a hard problem.
- Assert gradients flow: after one backward pass, every trainable parameter's `.grad` is non-`None` where the op is differentiable.
- Fix the seed and run on CPU in tests; a GPU-only or unseeded test is not repeatable (F.I.R.S.T.).
- Test a custom `Dataset`/`DataLoader` pair apart from the model: assert batch shape, dtype, and that a transform changed the data.

## Enforce

- Ruff `NPY002` (`np.random` calls) plus the complexity and unused-argument rules from the Python pack.
- mypy or pyright on `models/` and `training/`; a `forward`/`__getitem__` signature is the easiest place to leave a shape untyped and wrong.
- pytest-randomly to surface a test that passes for one seed; reproduce a failure with the seed it reports, never rerun until green (G4, T7).
- import-linter for the layers contract above, where declared.

## Smells

- A hard-coded `.cuda()` or `.to("cuda")` that crashes the script on a CPU-only machine (G35).
- Evaluation run without `model.eval()`, or without `no_grad`/`inference_mode`, silently keeping dropout and gradient tracking on (G3).
- The model pickled with `torch.save(model)` instead of its `state_dict`, tying every checkpoint to one class path.
- An unseeded `DataLoader` worker or sampler turning a concurrency bug into a "flaky" test (F.I.R.S.T., T7).
- A hyperparameter or path buried inside a model or training function instead of `configs/` (G35, G25).
- A hand-rolled training loop duplicating what the project's Lightning `Trainer` does (G5).
