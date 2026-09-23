# Spring

> Applies to: Spring Framework 6 and 7; Spring Boot 3 and 4 (Framework 7 / Boot 4 reached GA in November 2025). Language pack: `languages/java.md`. Read with: nothing.

## Structure

- `src/main/java/.../<feature>/` grouped by feature, or the classic `controller/`, `service/`, `repository/`, `entity/` (or `model/`), `dto/` layer folders for a smaller service.
- `src/main/java/.../advice/` (often beside `exception/`) — `@RestControllerAdvice` classes that turn exceptions into responses.
- `src/main/java/.../config/` — `@Configuration` classes: bean wiring and framework setup only, never a business rule.
- `src/main/resources/application.yml` plus `application-<profile>.yml` — externalized configuration; `src/main/resources/db/migration/` — Flyway (or `db/changelog/` for Liquibase) versioned schema changes.
- `src/test/java/...` mirrors `main`; reserve `@SpringBootTest` for full-context tests and prefer a slice test (`@WebMvcTest`, `@DataJpaTest`) for one layer at a time.
- The `@SpringBootApplication` class is the composition root: it starts the context and holds no business rule.

## Roles

```clean-roles
role advice = **/advice/**, **/exception/**
role entity = **/entity/**, **/entities/**, **/model/**, **/models/**
signal advice = @(?:Rest)?ControllerAdvice\b
signal controller = @(?:Rest)?Controller\b
signal service = @Service\b
signal repository = @Repository\b|extends\s+\w*Repository<
signal entity = @Entity\b|@Document\b
signal config = @Configuration\b|@ConfigurationProperties\b
```

## Rules

- Inject every dependency through the constructor onto a `final` field; Spring wires a class's sole constructor with no `@Autowired` needed, and field injection hides a class's real dependencies from its own tests (G8).
- Put `@Transactional` on public service methods, never on a controller or a private method: Spring's proxy cannot intercept a call that never arrives through it, so a private `@Transactional` method silently runs with no transaction at all (G2).
- Never call an `@Transactional` method on `this`; self-invocation bypasses the proxy the same way a private method does — move the method to a collaborator bean.
- Keep JPA entities out of the controller's request and response types; map to and from a DTO at the web boundary so a column rename cannot change the API (G8).
- Centralize exception-to-response mapping in one `@RestControllerAdvice`; do not repeat the same `try`/`catch` in every controller method (G5).
- Validate an incoming request body with Jakarta Bean Validation (`@Valid` plus constraint annotations) at the controller; do not hand-check fields again in the service.
- Let a circular bean dependency fail fast instead of breaking it open with `@Lazy`: two beans that need each other directly are a design problem, not a wiring inconvenience (G13).
- On Spring Framework 7, annotate nullable parameters and returns with `org.jspecify.annotations.Nullable`; Spring's own `@Nullable` is deprecated in its favor.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Servlet, JPA, and messaging types (`HttpServletRequest`, `ResponseEntity`, `@Entity`, a Spring Data repository) never cross into the domain or application layer (the Dependency Rule).
- Declare a port as a plain interface in the application layer; a `@Repository` or `@Service` adapter class implements it, named for the technology it wraps.
- The `@SpringBootApplication` class and the `@Configuration` classes are the composition root: the only place allowed to wire a concrete adapter to the port it implements.

```clean-architecture
layer domain      = src/main/java/**/domain/**
layer application = src/main/java/**/application/**
layer persistence = src/main/java/**/persistence/**, src/main/java/**/repository/**
layer web         = src/main/java/**/web/**, src/main/java/**/controller/**
layer main        = src/main/java/**/*Application.java, src/main/java/**/config/**
```

## Tests

- Prefer a slice test (`@WebMvcTest`, `@DataJpaTest`) over `@SpringBootTest`; it boots less context and fails closer to the cause.
- Mock a collaborator bean with `@MockitoBean` / `@MockitoSpyBean`, not the deprecated `@MockBean` / `@SpyBean`.
- Run an integration test against a real database or broker with Testcontainers instead of an embedded fake.
- With Spring Modulith, verify the module graph with `ApplicationModules.of(Application.class).verify()` and slice an integration test to one module with `@ApplicationModuleTest`.

## Enforce

- ArchUnit `layeredArchitecture()` for the declared layers, plus a `noClasses()...resideInAPackage("..domain..").should().dependOnClassesThat().resideInAPackage("..web..")` rule for the direction that matters most.
- ArchUnit `noFields().should().beAnnotatedWith(Autowired.class)` to fail the build the moment field injection appears.
- Spring Modulith `ApplicationModules.of(Application.class).verify()`, run as a JUnit 5 test, for module boundaries.
- Checkstyle and PMD from the Java pack apply unchanged; this framework adds no linter of its own.

## Smells

- Field injection instead of a constructor parameter, hiding what a class actually depends on (G8).
- `@Transactional` on a private method, or reached only through self-invocation, so no transaction ever opens (G2).
- Two `@Service` beans injecting each other directly, kept alive only by `@Lazy` (G13).
- A JPA `@Entity` returned or accepted directly by a `@RestController`, coupling the wire format to the schema (G8).
- A god `@Service` that has absorbed every rule in the module because it was already injected everywhere (G17, SRP).
