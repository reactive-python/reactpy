# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Using the following categories, list your changes in this order:
[Added, Changed, Deprecated, Removed, Fixed, Security]

Don't forget to remove deprecated code on each major release!
-->

## [Unreleased]

### Added

- Added support for Python 3.12, 3.13, and 3.14.
- Added type hints to `reactpy.html` attributes.
- Added support for nested components in web modules
- Added support for inline JavaScript as event handlers or other attributes that expect a callable via `reactpy.types.InlineJavaScript`
- Event functions can now call `event.preventDefault()` and `event.stopPropagation()` methods directly on the event data object, rather than using the `@event` decorator.
- Event data now supports accessing properties via dot notation (ex. `event.target.value`).
- Added support for partial functions in EventHandler
- Added `reactpy.types.Event` to provide type hints for the standard `data` function argument (for example `def on_click(event: Event): ...`).
- Added `asgi` and `jinja` installation extras (for example `pip install reactpy[asgi, jinja]`).
- Added `reactpy.executors.asgi.ReactPy` that can be used to run ReactPy in standalone mode via ASGI.
- Added `reactpy.executors.asgi.ReactPyCsr` that can be used to run ReactPy in standalone mode via ASGI, but rendered entirely client-sided.
- Added `reactpy.executors.asgi.ReactPyMiddleware` that can be used to utilize ReactPy within any ASGI compatible framework.
- Added `reactpy.templatetags.ReactPyJinja` that can be used alongside `ReactPyMiddleware` to embed several ReactPy components into your existing application. This includes the following template tags: `{% component %}`, `{% pyscript_component %}`, and `{% pyscript_setup %}`.
- Added `reactpy.pyscript_component` that can be used to embed ReactPy components into your existing application.
- Added `reactpy.use_async_effect` hook.
- Added `reactpy.Vdom` primitive interface for creating VDOM dictionaries.
- Added `reactpy.reactjs.component_from_file` to import ReactJS components from a file.
- Added `reactpy.reactjs.component_from_url` to import ReactJS components from a URL.
- Added `reactpy.reactjs.component_from_string` to import ReactJS components from a string.
- Added `reactpy.reactjs.component_from_npm` to import ReactJS components from NPM.
- Added `reactpy.h` as a shorthand alias for `reactpy.html`.

### Changed

- The `key` attribute is now stored within `attributes` in the VDOM spec.
- Substitute client-side usage of `react` with `preact`.
- Script elements no longer support behaving like effects. They now strictly behave like plain HTML scripts.
- The `reactpy.html` module has been modified to allow for auto-creation of any HTML nodes. For example, you can create a `<data-table>` element by calling `html.data_table()`.
- Change `set_state` comparison method to check equality with `==` more consistently.
- Add support for rendering `@component` children within `vdom_to_html`.
- Renamed the `use_location` hook's `search` attribute to `query_string`.
- Renamed the `use_location` hook's `pathname` attribute to `path`.
- Renamed `reactpy.config.REACTPY_DEBUG_MODE` to `reactpy.config.REACTPY_DEBUG`.
- ReactPy no longer auto-converts `snake_case` props to `camelCase`. It is now the responsibility of the user to ensure that props are in the correct format.
- Rewrite the `event-to-object` package to be more robust at handling properties on events.
- Custom JS components will now automatically assume you are using ReactJS in the absence of a `bind` function.
- Refactor layout rendering logic to improve readability and maintainability.
- The JavaScript package `@reactpy/client` now exports `React` and `ReactDOM`, which allows third-party components to re-use the same React instance as ReactPy.
- `reactpy.html` will now automatically flatten lists recursively (ex. `reactpy.html(["child1", ["child2"]])`)
- `reactpy.utils.reactpy_to_string` will now retain the user's original casing for `data-*` and `aria-*` attributes.
- `reactpy.utils.string_to_reactpy` has been upgraded to handle more complex scenarios without causing ReactJS rendering errors.
- `reactpy.core.vdom._CustomVdomDictConstructor` has been moved to `reactpy.types.CustomVdomConstructor`.
- `reactpy.core.vdom._EllipsisRepr` has been moved to `reactpy.types.EllipsisRepr`.
- `reactpy.types.VdomDictConstructor` has been renamed to `reactpy.types.VdomConstructor`.
- `REACTPY_ASYNC_RENDERING` can now de-duplicate and cascade renders where necessary.
- `REACTPY_ASYNC_RENDERING` is now defaulted to `True` for up to 40x performance improvements in environments with high concurrency.

### Deprecated

- `reactpy.web.module_from_file` is deprecated. Use `reactpy.reactjs.component_from_file` instead.
- `reactpy.web.module_from_url` is deprecated. Use `reactpy.reactjs.component_from_url` instead.
- `reactpy.web.module_from_string` is deprecated. Use `reactpy.reactjs.component_from_string` instead.
- `reactpy.web.export` is deprecated. Use `reactpy.reactjs.component_from_*` instead.
- `reactpy.web.*` is deprecated. Use `reactpy.reactjs.*` instead.

### Removed

- Removed support for Python 3.9 and 3.10.
- Removed the ability to import `reactpy.html.*` elements directly. You must now call `html.*` to access the elements.
- Removed backend specific installation extras (such as `pip install reactpy[starlette]`).
- Removed support for async functions within `reactpy.use_effect` hook. Use `reactpy.use_async_effect` instead.
- Removed deprecated function `module_from_template`.
- Removed deprecated exception type `reactpy.core.serve.Stop`.
- Removed deprecated component `reactpy.widgets.hotswap`.
- Removed `reactpy.sample` module.
- Removed `reactpy.svg` module. Contents previously within `reactpy.svg.*` can now be accessed via `reactpy.html.svg.*`.
- Removed `reactpy.html._` function. Use `reactpy.html(...)` or `reactpy.html.fragment(...)` instead.
- Removed `reactpy.run`. See the documentation for the new method to run ReactPy applications.
- Removed `reactpy.backend.*`. See the documentation for the new method to run ReactPy applications.
- Removed `reactpy.core.types` module. Use `reactpy.types` instead.
- Removed `reactpy.utils.html_to_vdom`. Use `reactpy.utils.string_to_reactpy` instead.
- Removed `reactpy.utils.vdom_to_html`. Use `reactpy.utils.reactpy_to_string` instead.
- Removed `reactpy.vdom`. Use `reactpy.Vdom` instead.
- Removed `reactpy.core.make_vdom_constructor`. Use `reactpy.Vdom` instead.
- Removed `reactpy.core.custom_vdom_constructor`. Use `reactpy.Vdom` instead.
- Removed `reactpy.Layout` top-level re-export. Use `reactpy.core.layout.Layout` instead.
- Removed `reactpy.types.LayoutType`. Use `reactpy.types.BaseLayout` instead.
- Removed `reactpy.types.ContextProviderType`. Use `reactpy.types.ContextProvider` instead.
- Removed `reactpy.core.hooks._ContextProvider`. Use `reactpy.types.ContextProvider` instead.
- Removed `reactpy.web.utils`. Use `reactpy.reactjs.utils` instead.

### Fixed

- Fixed a bug where script elements would not render to the DOM as plain text.
- Fixed a bug where the `key` property provided within server-side ReactPy code was failing to propagate to the front-end JavaScript components.
- Fixed a bug where `RuntimeError("Hook stack is in an invalid state")` errors could be generated when using a webserver that reuses threads.
- Allow for ReactPy and ReactJS components to be arbitrarily inserted onto the page with any possible hierarchy.

## [1.1.0] - 2024-11-24

### Fixed

- Fixed broken `module_from_template` due to a recent release of `requests`.
- Fixed `module_from_template` not working when using Flask backend.
- Fixed `UnicodeDecodeError` when using `reactpy.web.export`.
- Fixed needless unmounting of JavaScript components during each ReactPy render.
- Fixed missing `event["target"]["checked"]` on checkbox inputs.
- Fixed missing static files on `sdist` Python distribution.

### Added

- Allow concurrently rendering discrete component trees - enable this experimental feature by setting `REACTPY_ASYNC_RENDERING=true`. This improves the overall responsiveness of your app in situations where larger renders would otherwise block smaller renders from executing.

### Changed

- Previously `None`, when present in an HTML element, would render as the string `"None"`. Now `None` will not render at all. This is now equivalent to how `None` is handled when returned from components.
- Move hooks from `reactpy.backend.hooks` into `reactpy.core.hooks`.

### Deprecated

- The `Stop` exception. Recent releases of `anyio` have made this exception difficult to use since it now raises an `ExceptionGroup`. This exception was primarily used for internal testing purposes and so is now deprecated.
- Deprecate `reactpy.backend.hooks` since the hooks have been moved into `reactpy.core.hooks`.

## [1.0.2] - 2023-07-03

### Fixed

- Fix rendering bug when children change positions.

## [1.0.1] - 2023-06-16

### Changed

- Warn and attempt to fix missing mime types, which can result in `reactpy.run` not working as expected.
- Rename `reactpy.backend.BackendImplementation` to `reactpy.backend.BackendType`.
- Allow `reactpy.run` to fail in more predictable ways.

### Fixed

- Better traceback for JSON serialization errors.
- Explain that JS component attributes must be JSON.
- Fix `reactpy.run` port assignment sometimes attaching to in-use ports on Windows.
- Fix `reactpy.run` not recognizing `fastapi`.

## [1.0.0] - 2023-03-14

### Changed

- Reverts PR 841 as per the conclusion in discussion 916, but preserves the ability to declare attributes with snake_case.
- Reverts PR 886 due to issue 896.
- Revamped element constructor interface. Now instead of passing a dictionary of attributes to element constructors, attributes are declared using keyword arguments. For example, instead of writing:

### Deprecated

- Declaration of keys via keyword arguments in standard elements. A script has been added to automatically convert old usages where possible.

### Removed

- Accidental import of reactpy.testing.

### Fixed

- Minor issues with camelCase rewrite CLI utility.
- Minor type hint issue with `VdomDictConstructor`.
- Stale event handlers after disconnect/reconnect cycle.
- Fixed CLI not registered as entry point.
- Unification of component and VDOM constructor interfaces.

[Unreleased]: https://github.com/reactive-python/reactpy/compare/reactpy-v1.1.0...HEAD
[1.1.0]: https://github.com/reactive-python/reactpy/compare/reactpy-v1.0.2...reactpy-v1.1.0
[1.0.2]: https://github.com/reactive-python/reactpy/compare/reactpy-v1.0.1...reactpy-v1.0.2
[1.0.1]: https://github.com/reactive-python/reactpy/compare/reactpy-v1.0.0...reactpy-v1.0.1
[1.0.0]: https://github.com/reactive-python/reactpy/compare/0.44.0...reactpy-v1.0.0
[0.44.0]: https://github.com/reactive-python/reactpy/compare/0.43.0...0.44.0
[0.43.0]: https://github.com/reactive-python/reactpy/compare/0.42.0...0.43.0
[0.42.0]: https://github.com/reactive-python/reactpy/compare/0.41.0...0.42.0
[0.41.0]: https://github.com/reactive-python/reactpy/compare/0.40.2...0.41.0
[0.40.2]: https://github.com/reactive-python/reactpy/compare/0.40.1...0.40.2
[0.40.1]: https://github.com/reactive-python/reactpy/compare/0.40.0...0.40.1
[0.40.0]: https://github.com/reactive-python/reactpy/compare/0.39.0...0.40.0
[0.39.0]: https://github.com/reactive-python/reactpy/compare/0.38.1...0.39.0
[0.38.1]: https://github.com/reactive-python/reactpy/compare/0.38.0...0.38.1
[0.38.0]: https://github.com/reactive-python/reactpy/compare/0.37.2...0.38.0
[0.37.2]: https://github.com/reactive-python/reactpy/compare/0.37.1...0.37.2
[0.37.1]: https://github.com/reactive-python/reactpy/compare/0.37.0...0.37.1
[0.37.0]: https://github.com/reactive-python/reactpy/compare/0.36.3...0.37.0
[0.36.3]: https://github.com/reactive-python/reactpy/compare/0.36.2...0.36.3
[0.36.2]: https://github.com/reactive-python/reactpy/compare/0.36.1...0.36.2
[0.36.1]: https://github.com/reactive-python/reactpy/compare/0.36.0...0.36.1
[0.36.0]: https://github.com/reactive-python/reactpy/compare/0.35.4...0.36.0
[0.35.4]: https://github.com/reactive-python/reactpy/compare/0.35.3...0.35.4
[0.35.3]: https://github.com/reactive-python/reactpy/compare/0.35.2...0.35.3
[0.35.2]: https://github.com/reactive-python/reactpy/compare/0.35.1...0.35.2
[0.35.1]: https://github.com/reactive-python/reactpy/compare/0.35.0...0.35.1
[0.35.0]: https://github.com/reactive-python/reactpy/compare/0.34.0...0.35.0
[0.34.0]: https://github.com/reactive-python/reactpy/compare/0.33.3...0.34.0
[0.33.3]: https://github.com/reactive-python/reactpy/compare/0.33.2...0.33.3
[0.33.2]: https://github.com/reactive-python/reactpy/compare/0.33.1...0.33.2
[0.33.1]: https://github.com/reactive-python/reactpy/compare/0.33.0...0.33.1
[0.33.0]: https://github.com/reactive-python/reactpy/compare/0.32.0...0.33.0
[0.32.0]: https://github.com/reactive-python/reactpy/compare/0.31.0...0.32.0
[0.31.0]: https://github.com/reactive-python/reactpy/compare/0.30.1...0.31.0
[0.30.1]: https://github.com/reactive-python/reactpy/compare/0.30.0...0.30.1
[0.30.0]: https://github.com/reactive-python/reactpy/compare/0.29.0...0.30.0
[0.29.0]: https://github.com/reactive-python/reactpy/compare/0.28.0...0.29.0
[0.28.0]: https://github.com/reactive-python/reactpy/compare/0.27.0...0.28.0
[0.27.0]: https://github.com/reactive-python/reactpy/compare/0.26.0...0.27.0
[0.26.0]: https://github.com/reactive-python/reactpy/compare/0.25.0...0.26.0
[0.25.0]: https://github.com/reactive-python/reactpy/compare/0.24.0...0.25.0
[0.24.0]: https://github.com/reactive-python/reactpy/compare/0.23.1...0.24.0
[0.23.1]: https://github.com/reactive-python/reactpy/compare/0.23.0...0.23.1
[0.23.0]: https://github.com/reactive-python/reactpy/releases/tag/0.23.0
