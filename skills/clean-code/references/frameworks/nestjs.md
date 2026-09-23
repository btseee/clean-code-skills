# NestJS

> Applies to: NestJS 10 through 12 (12 current since August 2026). Language pack: `typescript.md`. Read with: nothing.

## Structure

- `src/main.ts` — bootstraps the application; the composition root for global pipes, filters, guards, and interceptors.
- `src/app.module.ts` — the root module; imports every feature module.
- `src/<feature>/<feature>.module.ts` — wires one feature's controllers and providers together.
- `src/<feature>/<feature>.controller.ts` — routes; parses the request via DTOs and delegates to the service.
- `src/<feature>/<feature>.service.ts` — `@Injectable()`; the feature's business rules.
- `src/<feature>/dto/` — request and response shapes, validated at the boundary.
- `src/<feature>/entities/` — persistence models (TypeORM, Prisma, or Mongoose); a detail, not a domain type.
- `src/common/` (`guards/`, `interceptors/`, `pipes/`, `filters/`) — cross-cutting concerns shared by more than one feature; keep a feature-only one beside its feature instead.

## Roles

```clean-roles
signal module [ts] = @Module\(
signal controller [ts] = @Controller\(
signal guard [ts] = implements\s+CanActivate
signal interceptor [ts] = implements\s+NestInterceptor
signal pipe [ts] = implements\s+PipeTransform
signal filter [ts] = @Catch\(|implements\s+ExceptionFilter
signal middleware [ts] = implements\s+NestMiddleware
signal resolver [ts] = @Resolver\(
signal gateway [ts] = @WebSocketGateway
signal entity [ts] = @Entity\(
signal service [ts] = @Injectable\(
role module = **/*.module.ts
role guard = **/*.guard.ts
role interceptor = **/*.interceptor.ts
role pipe = **/*.pipe.ts
role filter = **/*.filter.ts
role resolver = **/*.resolver.ts
role gateway = **/*.gateway.ts
role entity = **/*.entity.ts, **/entities/**
```

## Rules

- Keep a controller to routing only: validate via a DTO or pipe, call one service method, return its result; no business rule inside a controller (G17).
- Keep guards, interceptors, pipes, and filters single-purpose: a guard decides yes or no, an interceptor wraps, a pipe transforms or validates, a filter maps an exception to a response — never smuggle a business rule into any of them (G17).
- Validate and shape input at the boundary with DTOs and pipes (`ValidationPipe`, or on NestJS 12 the `schema` option of `@Body()`/`@Query()`/`@Param()` with a registered `StandardSchemaValidationPipe`, for Zod, Valibot, or ArkType); a service receives already-valid data.
- Never return a persistence entity straight from a controller; map it to a DTO so the wire format and the storage schema can change independently (DTO).
- Inject dependencies through the constructor. Reach for `forwardRef()` only when two providers or modules truly need each other, and treat a growing web of them as a sign that a shared abstraction is missing (G13).
- Wire global pipes, filters, guards, and interceptors once in `main.ts`; do not scatter equivalent registrations across feature modules (Main as the ultimate detail).
- Keep a module's `providers` limited to what its own feature owns; import another feature's module to reuse its exports instead of redeclaring the same provider (G5).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- An `@Entity()` class is a persistence detail, not a domain entity: TypeORM/Prisma/Mongoose types, `Request`/`Response`, and Nest's `ExecutionContext` never cross into business rules (the Dependency Rule).
- Declare repository and outbound-service ports as abstract classes or injection tokens in the application layer; providers under `infrastructure/` implement them and are bound with `useClass` in the module that owns them.
- `AppModule` and `main.ts` are the composition root: every provider binding lives there or in the feature module it belongs to, never inside a service.

```clean-architecture
layer domain         = **/domain/**
layer application    = src/**/*.service.ts
layer infrastructure = src/**/*.entity.ts, src/**/*.repository.ts
layer delivery       = src/**/*.controller.ts, src/**/*.resolver.ts, src/**/*.gateway.ts, src/**/*.guard.ts, src/**/*.interceptor.ts, src/**/*.pipe.ts, src/**/*.filter.ts
layer main           = src/main.ts, src/**/*.module.ts
```

## Tests

- Unit-test services as plain classes; construct them directly, or via `Test.createTestingModule` when they need the DI container, with fakes for their dependencies.
- Test a guard's `canActivate` or a pipe's `transform` directly, with a hand-built `ExecutionContext` or `ArgumentMetadata`; no HTTP call needed for that.
- Reserve `@nestjs/testing`'s `createNestApplication` plus `supertest` for a handful of routes that prove the whole pipeline, not every branch.
- Fake the clock, queue, and outbound HTTP client at the provider boundary; never hit a real network or database from a unit test (F.I.R.S.T.).

## Enforce

- `@typescript-eslint` (via Nest's own `eslint-config` from `nest new`) plus the language pack's `strict` baseline.
- dependency-cruiser or `eslint-plugin-boundaries` forbidding `**/*.service.ts` from importing `@nestjs/platform-express`/`@nestjs/platform-fastify` or any `*.controller.ts`.
- `class-validator`/`class-transformer` DTOs, or NestJS 12's Standard Schema pipes, on every `@Body()`/`@Query()`/`@Param()`; no handler reads an unvalidated payload.

## Smells

- A growing web of `forwardRef()` calls between modules or providers instead of a shared abstraction (G13).
- A guard, pipe, or interceptor that queries the database or applies a business rule instead of deferring to a service (G17).
- An ORM entity returned or accepted as a controller's response or body type instead of a DTO (DTO).
- A controller method longer than its DTO and one service call, with the business logic leaking upward (G30).
- `providers` or `exports` arrays that grew because no one removed what an old feature no longer needs (G9).
