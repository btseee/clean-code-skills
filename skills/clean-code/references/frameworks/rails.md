# Ruby On Rails

> Applies to: Rails 7.2 through 8.1. Language pack: `ruby.md`. Read with: nothing.

## Structure

- `app/models/` — Active Record models and the domain rules belonging to them (the `model` role).
- `app/controllers/` — thin controllers: params in, one call out, one response (the `controller` role).
- `app/services/` — a multi-step business transaction not belonging to one model (the `service` role).
- `app/jobs/` — background work queued through Active Job (the `job` role).
- `app/mailers/` — outgoing email content and delivery (the `mailer` role).
- `app/channels/` — Action Cable connections and broadcasts (the `channel` role).
- `app/policies/` — authorization rules, one class per resource (the `policy` role).
- `app/helpers/` — view-only formatting helpers, never business rules (the `helper` role).
- `**/concerns/**` — mixins shared by several models or controllers (the `concern` role).
- `config/routes.rb` — the only place routes are declared; `db/schema.rb` — generated, never hand-edited.

## Roles

```clean-roles
role model = app/models/**
signal model = <\s*(?:ApplicationRecord|ActiveRecord::Base)
role controller = app/controllers/**
signal controller = <\s*(?:ApplicationController|ActionController::\w+)
role job = app/jobs/**
signal job = <\s*ApplicationJob
role mailer = app/mailers/**
signal mailer = <\s*ApplicationMailer
role channel = app/channels/**
signal channel = <\s*ApplicationCable::Channel
role policy = app/policies/**
signal policy = <\s*ApplicationPolicy
role helper = app/helpers/**
role service = app/services/**
role concern = app/models/concerns/**, app/controllers/concerns/**
entry app/serializers/**, app/helpers/**
ignore-name = ^(ApplicationRecord|ApplicationController|ApplicationJob|ApplicationMailer|ApplicationPolicy)$
```

## Rules

- Keep controllers thin: params in, one call to a model method or a service object, one response out; no query logic or branching business rules in an action (G30).
- Name a model singular (`Order`), a controller and table plural (`OrdersController`, `orders`), its file `orders_controller.rb`.
- Put a rule on the model when one object owns it; reach for a service object under `app/services/` when a transaction spans several models or an external call. Both homes are idiomatic Rails — choose by ownership, not habit.
- Never add an `after_create`, `after_save`, or `after_commit` callback to trigger a side effect that belongs to the use case (charging a card, sending an email, calling an API); call it explicitly from the action or the service (G31, G17).
- Filter params with `params.expect(...)` (Rails 8) or `params.require(...).permit(...)`; never pass raw `params` straight into `.new` or `.update` (G24).
- Add `includes`/`preload`/`eager_load` before a view or serializer walks an association in a loop; an unbatched query inside a loop is an N+1.
- Keep authorization out of the controller body: call a policy object (`UserPolicy.new(current_user, record).edit?`) instead of inlining a role check (G17).
- Validate on the model, not only in the controller or a form object, so invalid data cannot reach the database through another path (G5).
- Never rescue an exception in a controller only to render nothing; render a real error response or let Rails' exception handling produce one (G4).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Active Record models and controllers are the framework's persistence and delivery layer, not domain. When declared, move domain rules into plain Ruby objects under `app/domain/` or `lib/`, orchestrated by services under `app/services/`; let the model stay a thin persistence adapter.
- Declare a port as a role module or documented duck type in the domain; a model, a mailer, or an external API client implements it. Framework and ORM types (`ActiveRecord::Base`, `ActionController::Base`, a `params` hash) never cross into the domain layer (the Dependency Rule).
- Compose the object graph in a Rails initializer (`config/initializers/`); a domain object never queries `ActiveRecord` or instantiates a mailer.

```clean-architecture
layer domain      = app/domain/**, lib/**
layer application = app/services/**
layer adapters    = app/models/**, app/mailers/**, app/jobs/**
layer delivery    = app/controllers/**, app/channels/**
layer main        = config/initializers/**
```

## Tests

- Test business rules as plain Ruby objects or models with RSpec or Minitest, without booting the request stack when a unit test suffices (F.I.R.S.T.).
- Test controllers with request specs (`spec/requests`) asserting status and body, not controller internals.
- Use `ActiveJob::TestHelper` (`assert_enqueued_with`, `perform_enqueued_jobs`) instead of asserting on a job's internals.
- Stub third-party calls (WebMock or VCR); never let a test hit a real external API.
- Keep system specs (Capybara) for real user flows; never use one to verify a single business rule a model spec covers more cheaply (F.I.R.S.T.).

## Enforce

- `rubocop-rails` on top of RuboCop's core cops for Rails-specific offenses (`Rails/SkipsModelValidations`, `Rails/OutputSafety`, and similar).
- packwerk (`bin/packwerk check`) in CI once the project declares packages, so the boundary stays real instead of aspirational.
- Brakeman in CI for injection, mass-assignment, and unsafe-redirect findings; treat a new warning as a merge blocker, not noise to suppress.
- A schema-drift check (`bin/rails db:schema:dump` diffed in CI) so `schema.rb`/`structure.sql` never falls behind the migrations.

## Smells

- A callback chain on a model reaching into unrelated systems (email, billing, a third-party API) instead of one persistence concern (G17, G31).
- A controller action with conditional business logic instead of one call out (G30, G6).
- `params` passed straight into `.create`/`.update` with no `permit` (G24).
- A view or serializer looping over an association with no `includes`, producing N+1 queries.
- A concern hiding a god-model's methods instead of a real collaborator (G17, G8).
- A fat `ApplicationController` filter (`before_action`) making a business decision shared by unrelated controllers (G13).
