# Concurrency

Concurrency separates *what* is done from *when*, improving throughput and structure — and
introduces a defect class ordinary testing doesn't catch. Read this before touching anything that
runs in more than one thread, task, process, or request handler sharing state.

Defining property: a concurrency bug is not reliably reproducible. A system can pass every test
for a year and still be wrong.

## Myths worth naming

- **"Concurrency always improves performance."** Only when there's genuine wait time to reclaim.
- **"Design does not change."** Decoupling what from when changes the design substantially.
- **"The container or framework handles it."** You still must know what it guarantees, what it
  doesn't, and what your state does under concurrent access.
- **"Concurrency is not much extra work."** It adds a second correctness problem atop the first,
  plus overhead, plus non-deterministic failure.

## Defense principles

**Apply the Single Responsibility Principle.** Concurrency policy changes for its own reasons: its
own modules, separate from business logic — mixed threading/domain code can't be reasoned about
or tested as either.

**Limit the scope of shared data.** Every place shared mutable data is touched is a bug's possible
home. Copy where you can, default to immutable values, confine mutation to a few named spots —
races, deadlocks, and concurrent-update defects all trace to mutable variables; no mutable locks,
no deadlocks.

**Keep threads as independent as possible.** A task sharing nothing cannot race — prefer each unit
of work owning its data, returning results rather than sharing state.

**Know your library.** Use your platform's thread-safe collections, executors, and non-blocking
primitives instead of hand-rolled locks. Know which classes are explicitly *not* thread-safe, and
that composing two thread-safe calls isn't automatically one.

## The named execution models

Recognize which one you're in — each has a known failure and a known fix.

**Producer-Consumer.** Producers fill a bounded queue; consumers drain it, each side signaling the
other. Failures: lost signals (a consumer waiting forever) and a full queue silently blocking
producers. Design backpressure in, don't bolt it on after.

**Readers-Writers.** Many readers, occasional writers, one resource. Failures: stale reads from
starved writers, writer starvation from unlimited readers, throughput collapse from serializing to
dodge both. Decide deliberately which side may starve, and bound it.

**Dining Philosophers.** Several processes competing for several shared resources at once — the
shape of most real lock contention. Failures: deadlock, livelock, starvation. Fix with resource
ordering, not more locking.

Most concurrency problems are a variant of one of these three.

## Locking discipline

- **Synchronized methods don't compose.** Two-plus synchronized methods on one shared object
  invite subtle failure: each call is atomic, the sequence isn't. Provide one method for the whole
  sequence; choose client- or server-side locking deliberately, never by accident.
- **Keep critical sections small.** Locks are expensive; every section is a bottleneck and a
  deadlock risk. Guard only what preserves the invariant — never split one invariant across two
  sections just to shrink them.
- **Shutdown is hard to get right.** The usual deadlock: workers waiting on work that never
  arrives, a parent waiting on blocked children. Design and test shutdown early — source of "it
  hangs occasionally in production."

## The four conditions for deadlock

All four are required together; break any one to prevent it:

1. **Mutual exclusion** — a resource cannot be shared.
2. **Hold and wait** — a holder waits while acquiring another resource.
3. **No preemption** — a resource cannot be taken from its holder.
4. **Circular wait** — a cycle of processes each waiting on the next.

Usually you break hold-and-wait (acquire everything at once, release all on failure) or circular
wait (a global lock order); breaking mutual exclusion removes the sharing, and no-preemption means
timeouts and release — often the pragmatic fix.

## Testing threaded code — seven distinct tactics

A single unit test proves nothing here; the seventh tactic is the one that actually finds races:

1. **Treat spurious failures as threading defects, not noise.** Never re-run until green and move
   on — "flaky test" is a diagnosis nobody made.
2. **Get non-threaded logic working first**; don't debug two problems at once.
3. **Make thread count, queue size, and timing configurable**, so the same code runs
   single-threaded for logic tests, multi-threaded for stress tests.
4. **Run with more threads than processors** — oversubscription forces more task switches where
   state is inconsistent.
5. **Run on different platforms**; scheduling differs by OS and runtime, and passing on one
   machine proves nothing.
6. **Force failures with deliberate jitter** — sleeps, yields, or priority changes at damaging
   points, by hand-placed hooks or an automated randomizing harness.
7. **Run the suite hundreds of times, and keep the failures** — jitter turns a one-in-a-million
   interleaving into a reproducible test.

## Throughput is a calculation, not a hope

Threads help throughput only in proportion to wait time reclaimed. Know your I/O-wait-to-
processing ratio before adding concurrency — mostly-processing work just adds contention and
overhead. Measure after adding it: a moved bottleneck isn't a removed one.

## Related

- `principles.md` — the summary rules for concurrency and state.
- `tests.md` — general test discipline; this file supersedes it for threaded code.
- `architecture.md` — why immutability and segregated mutability are architectural choices, and
  the decoupling modes that decide what shares an address space.
- `chapter-map.md` — the concurrency chapter checklist and the concurrency appendix.
