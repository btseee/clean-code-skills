# Agent Smells (A1-A10)

Failures that AI coding agents produce far more often than people do. They are not style problems:
each one is a way of being confidently wrong about the codebase. Cite them by ID (`A1`, `A7`) the
same way you cite `G17` or `T5`, and check yourself against them before claiming completion
(`session-protocol.md`, "Self-check").

Each entry: what it is, why agents produce it, how to spot it, what it looks like, what to do
instead, and what proves it is absent.

## A1 - Hallucinated API

**Definition.** Using a function, class, method, option, configuration key, CLI flag, or library
API without verifying that it exists in the installed version.

**Why agents produce it.** Training data blends versions and libraries; a plausible name is
generated with the same fluency as a real one, and memory of a newer or older release is
indistinguishable from knowledge of the installed one.

**Detection.**

- A call, import, decorator, or config key that appears nowhere in the dependency's source, type
  declarations, or documentation for the installed version.
- An API that exists in another major version of the same package.
- A flag or option the tool's `--help` does not list.
- The phrase "this should work" or "should be available" next to the call.

**Bad example.** `useFormState` from a React version that ships `useActionState`; a
`pandas.DataFrame.applymap` call against pandas 2.1 where it is deprecated in favour of `map`;
`axios.get(url, { retries: 3 })` when axios has no `retries` option.

**Preferred response.** Open the installed package (types, source, or `--help`) and confirm the
symbol and its signature. Record the version in `.clean/context.json` or `.clean/dependencies.json`
so the next session does not have to re-derive it. If the API does not exist, say so and use what
does.

**Verification.** Typecheck or compile where the language has one; otherwise a focused test that
actually calls the API, or a REPL probe quoted in the report.

## A2 - Unverified Dependency

**Definition.** Adding, upgrading, or relying on a package or version without checking that it is
installed, compatible, maintained, and actually needed.

**Why agents produce it.** A dependency is the fastest-looking path to a feature, and the cost of
adding one (install size, supply chain, version drift, a second way to do the same thing) is
invisible in the diff.

**Detection.**

- A new manifest entry with no matching lockfile change, or a lockfile change nobody asked for.
- A dependency added for something the standard library or an already-installed package does.
- A version pinned from memory rather than from the registry or the lockfile.
- Two packages in the manifest that solve the same problem.

**Bad example.** Adding `lodash` for one `debounce` when the project already has a `debounce` util;
bumping `react` in `package.json` to make a hook available without checking the peer dependencies.

**Preferred response.** Search the project and the installed dependencies first. If a new package
is genuinely needed, name the reason, check the installed ecosystem's conventions, and let the
package manager pin the version. Version upgrades are a user decision, recorded in
`.clean/decisions.md`.

**Verification.** Install succeeds from a clean state, the lockfile is consistent, and the build or
typecheck passes.

## A3 - Context Loss

**Definition.** Acting without the project's recorded context: the declared layers, past
decisions, the trusted verify command, conventions, or an in-flight campaign.

**Why agents produce it.** Sessions start from nothing. Whatever is not read from disk in the
first minutes does not exist, and the agent will re-derive a plausible, different answer.

**Detection.**

- A change that contradicts `.clean/decisions.md` or `.clean/architecture.md`.
- Re-asking a question `.clean/` already answers, or re-detecting a stack that is recorded.
- Restarting a cleanup campaign whose ledger shows it mid-flight.
- Running a verify command other than the one the project trusts.

**Bad example.** Introducing a repository interface the decisions log rejected two months ago; a
session that runs `npm test` while `.clean/commands.json` says `yarn test --runInBand`.

**Preferred response.** Read `.clean/` and the project's own instruction files before deciding
anything (`session-protocol.md`, step 1). A recorded decision is settled; if it looks wrong, say so
and let the user decide.

**Verification.** The handoff report names which context files were read. Decisions made this
session are appended, not silently re-decided.

## A4 - Scope Creep

**Definition.** Changing lines the task did not require: drive-by renames, reformatting,
dependency bumps, refactors of adjacent code, "while I'm here" cleanups.

**Why agents produce it.** Every smell in view looks cheap to fix, and there is no felt cost to a
larger diff. The reviewer pays it instead.

**Detection.**

- Changed lines that do not trace to the request or to cleanup the request caused.
- Files in the diff the task never named and the change never needed.
- Formatting churn from a different formatter or setting.
- A commit message that lists more than one intent.

**Bad example.** A bug fix in `pricing.ts` that also renames three parameters in `cart.ts`,
reorders imports across the package, and bumps `typescript`.

**Preferred response.** Surgical mode is the default: fix the task, report unrelated smells
separately. Whole-module cleanup happens only on explicit request, following
`project-refactor.md`.

**Verification.** Read the diff file by file and justify each hunk against the request. Anything
that cannot be justified is reverted or moved to a separate change.

## A5 - Duplicate Implementation

**Definition.** Writing logic, a helper, a type, or a whole file that already exists in the
project or in an installed dependency.

**Why agents produce it.** Writing is cheaper than searching. The agent does not know what it has
not read, and a fresh implementation always looks like progress.

**Detection.**

- A new function whose name or body resembles an existing one (`formatDate`, `slugify`,
  `retry`, `isEmpty`).
- A sibling-variant file: `_v2`, `_new`, `_final`, `_copy`, `_enhanced`, a date suffix.
- A second DTO or model for a concept that already has one, with no stated owner.
- A hand-rolled version of something the installed framework provides.

**Bad example.** `src/utils/dateFormat.ts` added beside an existing `src/lib/formatDate.ts`;
`OrderServiceV2` next to `OrderService`.

**Preferred response.** Search before writing: names, signatures, and behaviour. Extend the
existing owner; edit the original rather than create a sibling. Deduplicate only true duplication
(copies that must always change together).

**Verification.** `scripts/scan_repo.py` reports sibling variants and junk drawers; a grep for the
new function's name and its obvious synonyms returns only the new definition.

## A6 - Wrong-File Gravity

**Definition.** Placing code or files by convenience rather than responsibility: at the repository
root, in the current directory, in the file that happened to be open, or in a junk drawer.

**Why agents produce it.** The open file is the path of least resistance, and the project's layout
conventions are not in the prompt unless someone puts them there.

**Detection.**

- A new file at the repository root or in the working directory rather than where similar files
  live.
- Behaviour added to a controller, view, script, or test helper that belongs to a domain or
  application unit.
- Growth in `utils`, `helpers`, `common`, or `misc`.
- A new file that mirrors no existing artifact's location or naming pattern.

**Bad example.** Refund calculation added to `RefundController` because the controller was the
file being edited; `helpers.py` gaining a fourth unrelated function.

**Preferred response.** Follow the Placement Procedure in `SKILL.md`: find two or three similar
artifacts, mirror their location, naming, and registration, and route behaviour to the unit that
owns the responsibility. Record layout conventions in `.clean/conventions.json` so they are read,
not guessed.

**Verification.** `git status` shows new files only in conventional locations; each new unit
passes the one-sentence test; `scripts/check_boundaries.py` passes where layers are declared.

## A7 - Phantom Success

**Definition.** Claiming that code works, tests pass, or a command succeeded without having run
it, or presenting a stub, placeholder, or hardcoded demo value as finished work.

**Why agents produce it.** Producing the sentence "tests pass" is as easy as producing the code,
and the model's confidence in the code is not a measurement of it.

**Detection.**

- "This should work", "should now pass", "I have verified" without a quoted command and result.
- `pass`, `TODO`, `// in a real implementation`, `return mockData`, `NotImplementedError` in
  delivered code.
- A reported test run that does not match the project's verify command or its output shape.
- Green claimed while the CI or local run was never invoked.

**Bad example.** "I've added the migration and the tests pass" with no test output and a migration
that was never applied.

**Preferred response.** Run the check, quote the command and its result, and name what was not
run and what risk remains. Deliver working code or say plainly what is unfinished.

**Verification.** The handoff report contains the exact command and its verbatim result. If
verification could not run, the report says so and why.

## A8 - Test Weakening

**Definition.** Making a suite green by loosening assertions, skipping or deleting failing tests,
widening tolerances, mocking the unit under test, or catching the assertion error.

**Why agents produce it.** A red test reads as an obstacle to the task rather than as information
about it, and the fastest edit that removes red is to the test.

**Detection.**

- A failing test edited in the same change that was meant to fix production code.
- New `skip`, `xit`, `@pytest.mark.skip`, `.only`, or commented-out test bodies.
- Assertions changed from exact to loose (`toBeTruthy`, `assertIsNotNone`, wider `approx`).
- A mock of the very behaviour the test claims to check.
- Tests deleted with a message like "obsolete" and no replacement.

**Bad example.** Changing `expect(total).toBe(119.99)` to `expect(total).toBeGreaterThan(0)` to make
a rounding regression pass.

**Preferred response.** Fix the code, or report the conflict between the test and the request and
let the user decide. A test may change only when the behaviour it specified was intentionally
changed, and the change says so.

**Verification.** The diff to test files is reviewed separately; every loosened or removed
assertion is justified in the report. `scripts/scan_repo.py` counts skipped tests.

## A9 - Speculative Abstraction

**Definition.** Introducing an interface, layer, factory, plugin point, configuration system,
generic parameter, or service for a need nobody has yet.

**Why agents produce it.** Abstraction looks like good engineering, is easy to generate, and the
cost (indirection, one implementation behind an interface, a second place to change) lands on
future readers.

**Detection.**

- An interface with exactly one implementation and no test double that needs it.
- A factory, registry, strategy, or plugin mechanism with one product.
- Configuration for a value that never varies.
- A generic type with a single instantiation.
- "This will make it easier later" in the explanation.

**Bad example.** `IPaymentGatewayFactory` producing the only `StripeGateway`; a `NotificationChannel`
plugin system for the single email sender.

**Preferred response.** Build the concrete thing. Add the abstraction at the moment a second
implementation, a real test seam, or a genuine invariant demands it. Two adapters justify a seam;
one does not.

**Verification.** Every new interface or indirection in the diff has a named current consumer that
needs it. The deletion test: removing the abstraction should re-scatter complexity, not simply
shorten the code.

## A10 - Silent Architecture Drift

**Definition.** A change that crosses the declared or evident layering in the wrong direction (an
inner module naming an outer one, a controller reaching past the application layer, a detail type
travelling inward) without saying so.

**Why agents produce it.** The shortest wiring between two points is the default; the layer being
skipped is invisible in the two files being edited, and its purpose (often the only authorization
or validation) is not.

**Detection.**

- A new import in an inner layer that names an outer one: an ORM type, HTTP request, framework
  annotation, or infrastructure module in a domain or use-case file.
- A controller or handler calling a repository or client directly where existing code goes through
  a service or use case.
- A new dependency edge that `scripts/check_boundaries.py` reports, or that would if layers were
  declared.
- A framework base class under a business object.

**Bad example.** `OrdersController` importing `OrderRepository` when every other controller goes
through `OrderService`; `Order` entity gaining a `@Table` annotation.

**Preferred response.** Route the behaviour through the layer that owns it. If policy needs
something from a detail, declare the interface on the policy side and implement it outside. If
the layering itself must change, that is a user decision recorded in `.clean/decisions.md` and
`.clean/architecture.md`, not a side effect of a feature.

**Verification.** `scripts/check_boundaries.py` passes; where no layering is declared, the imports
of every changed inner file are listed in the report with the direction each one points.

## Cross-reference

| Concern | Related IDs |
| --- | --- |
| Verification honesty | A7, A8, A1 |
| Placement and structure | A6, A5, A9 |
| Dependencies and boundaries | A10, A2, A1 |
| Session discipline | A3, A4 |

The pre-3.3.0 "Agent Failure Modes" table in `SKILL.md` mapped onto these IDs as follows: invented
API and false completion are A1 and A7; reinvented helper and sibling-variant file are A5;
wrong-place file and nearest-file gravity are A6; shortest-path wiring, detail leaking inward, and
framework as architecture are A10; premature abstraction and eager deduplication are A9;
test-blessing and placeholder-as-done are A8 and A7; scope creep is A4; regeneration loss and
patch-without-understanding are A4 and A3; unwired artifact is A6.
