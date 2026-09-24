# WordPress

> Applies to: WordPress 6.x-7.x (7.1 is current). Language pack: `languages/php.md`. Read with: nothing.

## Structure

- `plugin-name.php` — header and bootstrap only: constants, the activation/deactivation hooks, a call into the main class.
- `includes/**` — environment-agnostic core classes: the main plugin class, its hook loader, activator, deactivator, i18n.
- `admin/**` — admin-screen classes, settings pages, and the assets they enqueue.
- `public/**` — front-end hooks, shortcodes, and the assets they enqueue.
- `blocks/**` or `src/blocks/**` — one folder per block: `block.json`, `render.php` or `index.js`, styles.
- `languages/**` — `.pot`/`.po`/`.mo` translation files.
- `tests/**` — the WordPress PHPUnit test suite, bootstrapped through `wp-env`.

## Roles

```clean-roles
role plugin-core = **/includes/**
role admin = **/admin/**
role frontend = **/public/**
role block = **/blocks/**
signal rest-controller = extends\s+WP_REST_Controller
signal widget = extends\s+WP_Widget
allow plugin-core = rest-controller, widget
```

## Rules

- Follow WordPress's own naming convention where `php.md`'s PSR style would otherwise apply: snake_case functions and methods (`get_user_settings()`), `Capitalized_Words` classes (`My_Plugin_Admin`), UPPER_SNAKE constants — this deliberately overrides PSR-1 in WordPress code (N3).
- Prefix every global — function, hook name, option key, transient key, class, constant — with the plugin's own prefix, or namespace it; an unprefixed `activate()` collides with any other plugin that declares one (G13).
- Sanitize every value read from `$_GET`, `$_POST`, or `$_REQUEST` on the way in (`sanitize_text_field()`, `absint()`, or another `sanitize_*` matching its shape); trust nothing from the request (G3).
- Escape every value on the way to output — `esc_html()`, `esc_attr()`, `esc_url()`, `esc_js()` — or run it through `wp_kses()`/`wp_kses_post()` when it must carry limited HTML; never `echo` a raw request or database value.
- Verify a nonce (`wp_verify_nonce()`, `check_admin_referer()`) and a capability (`current_user_can()`) before any state-changing action; missing either makes correct escaping moot.
- Build every query that includes a variable through `$wpdb->prepare()`; never interpolate a value directly into SQL (G26).
- Extend `WP_REST_Controller` for a REST endpoint and give every route a `permission_callback`; an omitted one defaults public and is a security hole, not a shortcut (G4).
- Declare a block's metadata in `block.json` with `"apiVersion": 3`, and build its assets with `@wordpress/scripts` rather than hand-rolled enqueue and localization code; from WordPress 7.1 the post editor is always iframed, whatever a block's `apiVersion`, so test every block inside the iframe.
- Autoload plugin classes through Composer PSR-4 (`"MyPlugin\\": "includes/"`); PSR-4 governs autoloading only, not the naming convention above.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Hook callbacks, shortcode handlers, REST controllers, and block render callbacks are delivery: they translate a WordPress request or lifecycle event into a call on a plain class.
- Business rules live in plain PHP classes under `includes/**` that take scalars or value objects, never a `WP_REST_Request`, `WP_Post`, or the global `$wpdb`.
- Declare an interface for `$wpdb`, the HTTP API, or an external SDK on the business side; implement and swap it in a class under `includes/**`, never inline in a hook callback.
- Register every hook from one place — the plugin's loader class or main file — never scattered `add_action()` calls inside a business class.

```clean-architecture
layer domain      = **/includes/Domain/**
layer application = **/includes/Services/**
layer delivery    = **/admin/**, **/public/**, **/blocks/**
layer main        = **/includes/class-*-loader.php
```

## Tests

- Bootstrap with `wp-env` (`@wordpress/env`) so tests run the real WordPress PHPUnit suite, not a hand-mocked `wp_*` shim.
- Test a hook's effect by firing it (`do_action()`, `apply_filters()`) and asserting the result, not that the callback was merely registered.
- Dispatch REST requests through `rest_do_request()` and assert status and body shape, including the unauthorized case (T5).
- Build fixtures with `WP_UnitTestCase`'s factories (`self::factory()->post->create()`); never seed through raw `$wpdb` inserts.

## Enforce

- PHP_CodeSniffer with WordPress Coding Standards (`wp-coding-standards/wpcs`): `WordPress-Extra` and `WordPress-Docs` beyond the core ruleset.
- `szepeviktor/phpstan-wordpress` with `php-stubs/wordpress-stubs`, so PHPStan resolves core functions and globals.
- `@wordpress/scripts` (`wp-scripts lint-js`, `lint-style`, `build`) for block and admin JavaScript/CSS.

## Smells

- An unprefixed function, class, or option name relying on luck, not a namespace or prefix, to avoid colliding (G13).
- `echo`/`print` of a `$_GET`/`$_POST`/post-meta value with no escaping function around it (G3).
- A form or `wp_ajax_*` action with no nonce check, no capability check, or both (G4).
- SQL built with string concatenation instead of `$wpdb->prepare()` placeholders (G26).
- Business logic inside a theme template instead of a filter the plugin owns (G17).
- A REST route with no `permission_callback`, or one hard-coded to `'__return_true'` (G4).
