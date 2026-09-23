# Pack Sources

The official documentation each pack's version-specific claims were checked against, so the next
maintainer can re-verify a pack when its language or framework ships a new major. Not shipped with
the skill and never loaded by an agent.

Re-check a pack when a new major of its subject appears, when a source below moves, or when an
agent reports an API the pack names as missing.

## Languages

### JavaScript (`languages/javascript.md`)

- ESLint 10 removes eslintrc; flat config only: <https://eslint.org/blog/2026/02/eslint-v10.0.0-released/>
- `Error` `cause` option: <https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Error/Error>
- Non-mutating array methods (`toSorted`, `toSpliced`, `with`): <https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Array/toSorted>

### TypeScript (`languages/typescript.md`)

- `erasableSyntaxOnly` (TypeScript 5.8): <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html>
- `baseUrl` deprecated (TypeScript 6.0): <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html>
- TypeScript 7.0, the native compiler: <https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/>
- typescript-eslint shared configs (`strict-type-checked`): <https://typescript-eslint.io/users/configs/>
- Node.js type stripping: <https://nodejs.org/api/typescript.html>

### Python (`languages/python.md`)

- Ruff rule codes (`C901`, `PLR0913`, `PLR0912`, `PLR0915`, `ARG001`, `ERA001`, `BLE001`, `S101`): <https://docs.astral.sh/ruff/rules/>
- `asyncio.TaskGroup` added in Python 3.11: <https://docs.python.org/3/library/asyncio-task.html>

### Java (`languages/java.md`)

- Java 25 LTS, GA 2025-09-16: <https://openjdk.org/projects/jdk/25/>
- Checkstyle `CyclomaticComplexity`/`MethodLength`: <https://checkstyle.sourceforge.io/checks/metrics/cyclomaticcomplexity.html>
- ArchUnit `layeredArchitecture()`: <https://www.archunit.org/userguide/html/000_Index.html>
- ArchUnit slices rules (`slices().matching(...)`): <https://www.archunit.org/userguide/html/000_Index.html#_slices>

### C (`languages/c.md`)

- C23 published as ISO/IEC 9899:2024: <https://www.iso.org/standard/82075.html>
- C23 `[[nodiscard]]` attribute: <https://en.cppreference.com/w/c/language/attributes/nodiscard>
- clang-tidy `readability-function-size`: <https://clang.llvm.org/extra/clang-tidy/checks/readability/function-size.html>
- GCC `-fanalyzer`: <https://gcc.gnu.org/onlinedocs/gccint/Static-Analyzer.html>

### C++ (`languages/cpp.md`)

- `misc-include-cleaner`: <https://clang.llvm.org/extra/clang-tidy/checks/misc/include-cleaner.html>
- `readability-function-cognitive-complexity` (default threshold 25): <https://clang.llvm.org/extra/clang-tidy/checks/readability/function-cognitive-complexity.html>
- `std::expected<T, E>` is a C++23 feature: <https://en.cppreference.com/cpp/header/expected>

### C# (`languages/csharp.md`)

- .NET 10 is LTS, GA 2025-11-11; .NET 8 and 9 both end support 2026-11-10: <https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/>
- C# language version defaults (.NET 8 to C# 12, .NET 9 to C# 13, .NET 10 to C# 14): <https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/configure-language-version>
- CA1502 threshold set in CodeMetricsConfig.txt; off by default: <https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca1502>
- NetArchTest.Rules / ArchUnitNET package names: <https://www.nuget.org/packages/NetArchTest.Rules/>
- `dotnet format --verify-no-changes` in CI: <https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-format>
- xUnit v3 runs on Microsoft Testing Platform: <https://xunit.net/docs/getting-started/v3/whats-new>

### PHP (`languages/php.md`)

- PHP 8.5 is current (released 2025-11-20): <https://php.watch/versions/8.5>
- PHP-CS-Fixer `@PER-CS` ruleset (PER Coding Style): <https://cs.symfony.com/doc/ruleSets/PER-CS.html>
- PHPStan levels 0-10, `max` alias: <https://phpstan.org/user-guide/rule-levels>

### Go (`languages/go.md`)

- Current stable release is Go 1.27: <https://go.dev/doc/devel/release>
- golangci-lint v2 config shape (linters split from formatters): <https://golangci-lint.run/docs/product/migration-guide/>
- `go-arch-lint` config (`.go-arch-lint.yml`): <https://github.com/fe3dback/go-arch-lint>

### Rust (`languages/rust.md`)

- Edition 2024 stable since rustc 1.85: <https://www.rustfaq.org/en/what-changed-in-rust-edition-2024/>
- Clippy restriction-group lints (`unwrap_used`, `expect_used`, `cognitive_complexity`): <https://doc.rust-lang.org/clippy/lints.html>
- `clippy.toml` / `[workspace.lints.clippy]` configuration: <https://doc.rust-lang.org/clippy/configuration.html>
- `cargo-deny`'s bans/licenses/advisories/sources checks: <https://docs.rs/cargo-deny>

### Swift (`languages/swift.md`)

- Swift 6.2 approachable concurrency (`@concurrent`, default main-actor isolation): <https://www.swift.org/blog/swift-6.2-released/>
- `swift-format` ships in the Swift toolchain: <https://github.com/swiftlang/swift-format>
- SwiftLint rule identifiers (`function_body_length`, `cyclomatic_complexity`, `function_parameter_count`, `force_unwrapping`, `force_try`): <https://realm.github.io/SwiftLint/rule-directory.html>
- Typed throws (SE-0413): <https://github.com/swiftlang/swift-evolution/blob/main/proposals/0413-typed-throws.md>

### Objective-C (`languages/objective-c.md`)

- `NS_ASSUME_NONNULL_BEGIN`/`END` convention: <https://developer.apple.com/documentation/foundation/ns_assume_nonnull_end>
- Nullability annotations and lightweight generics convention: <https://github.com/github/objective-c-style-guide/pull/63/files>

### Kotlin (`languages/kotlin.md`)

- Kotlin 2.x current release line: <https://kotlinlang.org/docs/releases.html>
- detekt complexity rules (`LongMethod`, `LongParameterList`, `CyclomaticComplexMethod`, `TooManyFunctions`): <https://detekt.dev/docs/rules/complexity/>
- Konsist architecture/structural linter: <https://docs.konsist.lemonappdev.com/>
- ktlint and ktfmt both current: <https://github.com/Kotlin/ktfmt>

### Ruby (`languages/ruby.md`)

- Ruby 4.0 is current, 3.4 in normal maintenance: <https://www.ruby-lang.org/en/news/2026/07/14/ruby-4-0-6-released/>
- Chilled strings in Ruby 3.4 (`frozen_string_literal`): <https://blog.saeloun.com/2024/05/20/frozen-string-literal/>
- RuboCop `Metrics/AbcSize`/`Metrics/CyclomaticComplexity` cops: <https://www.rubydoc.info/gems/rubocop/RuboCop/Cop/Metrics/AbcSize>
- Standard gem doesn't support RuboCop extensions: <https://github.com/standardrb/standard>
- packwerk is actively maintained: <https://rubygems.org/gems/packwerk>

### Shell (`languages/shell.md`)

- bats-core is the actively maintained testing fork: <https://github.com/bats-core/bats-core>

### PowerShell (`languages/powershell.md`)

- PowerShell 7.6 LTS support lifecycle: <https://learn.microsoft.com/en-us/powershell/scripting/install/powershell-support-lifecycle?view=powershell-7.6>
- PSScriptAnalyzer rule names: <https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules-recommendations?view=ps-modules>
- Pester 6.0.0 migration from v5 (existing `Should -Be` assertions keep working): <https://pester.dev/docs/migrations/v5-to-v6>

### R (`languages/r.md`)

- Current R release (4.6.1): <https://www.r-project.org/>
- testthat 3rd edition is current: <https://testthat.r-lib.org/articles/third-edition.html>
- lintr `cyclocomp_linter()`/`object_length_linter()`: <https://lintr.r-lib.org/reference/cyclocomp_linter.html>
- `usethis::use_testthat(3)` sets the 3e config: <https://usethis.r-lib.org/reference/use_testthat.html>
- `rlang::abort(..., parent = e)` chains a cause: <https://rlang.r-lib.org/reference/abort.html>
- `covr::package_coverage()` coverage entry point: <https://covr.r-lib.org/reference/package_coverage.html>
- `withr::local_*` scope-end restoration helpers: <https://withr.r-lib.org/reference/index.html>

### Dart (`languages/dart.md`)

- `unawaited_futures` lint rule: <https://dart.dev/tools/linter-rules/unawaited_futures>
- `package:lints` and `package:very_good_analysis` current: <https://pub.dev/packages/lints>

### Scala (`languages/scala.md`)

- Scala 3.9.0 is the new LTS line, succeeding 3.3.x: <https://scala-lang.org/news/3.9/>
- WartRemover cross-builds for Scala 3: <https://github.com/wartremover/wartremover>
- Scalafix has active Scala 3 support: <https://github.com/scalacenter/scalafix>

## Frameworks

### React (`frameworks/react.md`)

- React Compiler 1.0: <https://react.dev/blog/2025/10/07/react-compiler-1>
- `eslint-plugin-react-hooks` presets: <https://react.dev/reference/eslint-plugin-react-hooks>
- Effects only for synchronizing with external systems: <https://react.dev/learn/you-might-not-need-an-effect>
- `ref` as a prop in React 19: <https://react.dev/blog/2024/12/05/react-19>

### Next.js (`frameworks/nextjs.md`)

- fetch is no longer cached by default since Next.js 15: <https://nextjs.org/blog/next-15>
- `next lint` deprecated in 15.5: <https://nextjs.org/blog/next-15-5>
- Next.js 16: proxy.ts, Cache Components: <https://nextjs.org/blog/next-16>
- `proxy.ts` file convention: <https://nextjs.org/docs/app/api-reference/file-conventions/proxy>

### Vue and Nuxt (`frameworks/vue-nuxt.md`)

- Nuxt 4's `app/` directory default: <https://nuxt.com/blog/v4>
- Vue 3.5 `defineModel` (stable since 3.4): <https://blog.vuejs.org/posts/vue-3-5>

### Angular (`frameworks/angular.md`)

- Standalone is the default component API since v19: <https://blog.angular.dev/the-future-is-standalone-475d7edbc706>
- v20 drops generated `Component`/`Service`/`Directive`/`Pipe` suffixes by default: <https://blog.angular.dev/announcing-angular-v20-b5c9c06cf301>
- Zoneless change detection, stable via `provideZonelessChangeDetection`: <https://angular.dev/guide/zoneless>
- Angular 21: Vitest default test runner, zoneless by default: <https://blog.ninja-squad.com/2025/11/20/what-is-new-angular-21.0>
- Angular 22: OnPush default, `@Service()`, strictTemplates default, Fetch-backed HttpClient: <https://blog.ninja-squad.com/2026/06/03/what-is-new-angular-22.0>
- Angular v22 official announcement: <https://blog.angular.dev/announcing-angular-v22-c52bb83a4664>

### Svelte and SvelteKit (`frameworks/svelte.md`)

- SvelteKit hooks and request lifecycle: <https://svelte.dev/docs/kit/hooks>
- `$env/static/private` restricted to server modules: <https://svelte.dev/docs/kit/$env-static-private>

### Django (`frameworks/django.md`)

- Django 5.2 LTS / 6.1 current release train: <https://www.djangoproject.com/download/>
- Ruff `DJ` rules (`DJ001`, `DJ008`): <https://docs.astral.sh/ruff/rules/>

### Flask (`frameworks/flask.md`)

- Flask 3.x is current (3.1): <https://flask.palletsprojects.com/en/stable/changes/>

### FastAPI (`frameworks/fastapi.md`)

- FastAPI remains pre-1.0: <https://fastapi.tiangolo.com/release-notes/>
- Ruff `FAST` rules (`FAST001`-`FAST003`): <https://docs.astral.sh/ruff/rules/#fastapi-fast>
- `pydantic-settings` `BaseSettings`/`SettingsConfigDict`: <https://docs.pydantic.dev/latest/api/pydantic_settings/>
- import-linter `layers`/`forbidden` contract types: <https://import-linter.readthedocs.io/en/latest/contract_types.html>

### Express (`frameworks/express.md`)

- Express 5 auto-forwards async/thrown errors to `next(err)`: <https://expressjs.com/en/guide/error-handling.html>
- Express 5 migration (`/*splat` wildcards, `:file{.:ext}`, `extended: false` default): <https://expressjs.com/en/guide/migrating-5.html>
- Express 5.2.1 is the current published version: <https://registry.npmjs.org/express/latest>

### NestJS (`frameworks/nestjs.md`)

- NestJS 12 is current (since August 2026): <https://registry.npmjs.org/@nestjs/core/latest>
- NestJS 12 Standard Schema `schema` option with StandardSchemaValidationPipe: <https://github.com/nestjs/nest/releases/tag/v12.0.0>
- Guards (`@Injectable()` + `CanActivate`, `@UseGuards()`): <https://docs.nestjs.com/guards>
- Middleware (`NestMiddleware.use`, `MiddlewareConsumer`): <https://docs.nestjs.com/middleware>

### Strapi (`frameworks/strapi.md`)

- Strapi 5 project structure (`src/api/<name>/...`): <https://docs.strapi.io/cms/project-structure>
- `createCoreController` factory pattern: <https://docs.strapi.io/cms/backend-customization/controllers>
- Strapi 5 changed lifecycle-hook timing under the Document Service API: <https://strapi.io/blog/when-to-use-lifecycle-hooks-in-strapi>
- Strapi 5.55.0 is the current published version: <https://registry.npmjs.org/@strapi/strapi/latest>

### Spring (`frameworks/spring.md`)

- Spring Framework 7.0 / Boot 4.0 reached GA in November 2025: <https://spring.io/blog/2025/11/13/spring-framework-7-0-general-availability/>
- Spring Modulith `ApplicationModules.of(...).verify()`: <https://docs.spring.io/spring-modulith/reference/verification.html>
- Spring Modulith `@ApplicationModuleTest`: <https://docs.spring.io/spring-modulith/reference/testing.html>
- `@Transactional` proxy cannot intercept private methods or self-invocation: <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html>
- `@MockBean`/`@SpyBean` deprecated for `@MockitoBean`/`@MockitoSpyBean`: <https://springboot-123.mizucoffee.com/en/blog/spring-boot-mockbean-mockitobean-migration-guide/>
- `org.springframework.lang.Nullable` deprecated since Framework 7.0 in favor of jspecify: <https://docs.spring.io/spring-framework/reference/core/null-safety.html>
- ArchUnit `noFields().should().beAnnotatedWith(Autowired.class)`: <https://www.sivalabs.in/blog/impose-architecture-guidelines-using-archunit/>

### ASP.NET Core (`frameworks/aspnet-core.md`)

- .NET 8/9/10 support timeline (target .NET 10): <https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/>
- EF Core InMemory provider is not a relational simulation: <https://learn.microsoft.com/en-us/ef/core/providers/in-memory/>
- `AddDbContext` registers a scoped lifetime by default: <https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/>
- ProblemDetails / `IExceptionHandler` error handling (.NET 8+): <https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0>

### Laravel (`frameworks/laravel.md`)

- Laravel 12 release notes (Carbon 3, PHPUnit ^11 / Pest ^3): <https://laravel.com/docs/12.x/releases>
- Laravel 13 release notes (PHP 8.3 minimum, `#[Middleware]`/`#[Authorize]` attributes): <https://laravel.com/docs/13.x/releases>
- larastan is the maintained fork: <https://github.com/larastan/larastan>
- Pest architecture testing (`arch()`): <https://pestphp.com/docs/arch-testing>
- `app/Actions/**` convention (`lorisleiva/laravel-actions`): <https://laravelactions.com>
- Laravel Pint wraps PHP-CS-Fixer: <https://laravel.com/docs/pint>

### Symfony (`frameworks/symfony.md`)

- Symfony 7.4 LTS / 8.0 / 8.1 release and support timeline: <https://symfony.com/releases>
- `#[AsCommand]`/`#[AsMessageHandler]` autoconfigured attributes: <https://symfony.com/doc/current/service_container.html>
- Voters extend `Voter`: <https://symfony.com/doc/current/security/voters.html>
- Deptrac configuration (`deptrac.yaml`, layers + ruleset): <https://deptrac.github.io/deptrac/configuration>
- `phpstan/phpstan-symfony` extension: <https://github.com/phpstan/phpstan-symfony>

### Ruby on Rails (`frameworks/rails.md`)

- Rails 8.1 is current (released October 2025): <https://guides.rubyonrails.org/8_1_release_notes.html>
- `params.expect` (Rails 8.0): <https://guides.rubyonrails.org/action_controller_overview.html#strong-parameters>
- Brakeman is actively maintained, supports Rails 2.3.x-8.x: <https://brakemanscanner.org/>

### Gin and Beego (`frameworks/gin-beego.md`)

- Gin v1.12.0 is the current release: <https://github.com/gin-gonic/gin/releases>
- Beego v2.3.9 is the current release: <https://github.com/beego/beego/releases>
- Beego controller/router conventions (`web.Controller`, lifecycle methods): <https://beego.vip/docs/quickstart/controller.md>
- golangci-lint `contextcheck`/`bodyclose` linters: <https://golangci-lint.run/docs/linters/>

### Ktor (`frameworks/ktor.md`)

- Ktor 3.x is current (3.5.2): <https://ktor.io/docs/releases.html>
- `RequestValidation` plugin: <https://ktor.io/docs/server-request-validation.html>
- `StatusPages` plugin: <https://ktor.io/docs/server-status-pages.html>
- Built-in DI plugin (`io.ktor:ktor-server-di`): <https://ktor.io/docs/server-dependency-injection.html>
- `testApplication { }` test host: <https://ktor.io/docs/server-testing.html>

### Jetpack Compose (`frameworks/jetpack-compose.md`)

- Compose Compiler Gradle plugin (`org.jetbrains.kotlin.plugin.compose`): <https://developer.android.com/develop/ui/compose/compiler>
- `collectAsStateWithLifecycle()` as the recommended collector: <https://developer.android.com/topic/architecture/recommendations>
- `mrmans0n/compose-rules` maintained fork: <https://github.com/mrmans0n/compose-rules>

### SwiftUI and UIKit (`frameworks/swiftui-uikit.md`)

- `@Observable`/Observation framework (iOS 17+), replacing `ObservableObject`: <https://sarunw.com/posts/observation-framework-in-ios17/>
- `@Environment`/`@Bindable` injection pattern: <https://www.hackingwithswift.com/books/ios-swiftui/sharing-observable-objects-through-swiftuis-environment>

### Flutter (`frameworks/flutter.md`)

- `use_build_context_synchronously` lint rule: <https://dart.dev/tools/linter-rules/use_build_context_synchronously>
- `package:flutter_lints` current: <https://pub.dev/packages/flutter_lints>
