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
- Added `reactpy.config.REACTPY_MAX_QUEUE_SIZE` to configure the maximum size of all ReactPy asyncio queues (e.g. receive buffer, send buffer, event buffer) before ReactPy begins waiting until a slot frees up. This can be used to constraint memory usage.
- Events now support `debounce` and `throttle`, configurable per event via `event.debounce = <milliseconds>` and `EventHandler(fn, throttle=<milliseconds>)` respectively.
    - `debounce` waits until activity stops, then fires once. Default is 200 ms on `input`/`select`/`textarea`, 0 ms elsewhere.
    - `throttle` caps the rate how often an event is allowed to execute. No default; opt in per event.

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
- `REACTPY_ASYNC_RENDERING` can now de-duplicate renders where necessary.
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
- Removed `reactpy.utils.str_to_bool`.
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
- Fixed a bug where events on controlled inputs (e.g. `html.input({"onChange": ...})`) could be lost during rapid actions.
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

## [0.44.0] - 2023-01-27

### Deprecated

- `reactpy.widgets.hotswap`. The function has no clear uses outside of some internal applications.

### Removed

- Ability to access element value from events via `event['value']` key. Use `event['target']['value']` instead.
- Old misspelled option `REACTPY_WED_MODULES_DIR`.

## [0.43.0] - 2023-01-09

### Deprecated

- `ComponentType.()`. This method was implemented based on reading the React/Preact source code.

### Fixed

- Nested context does not update value if outer context should not render.
- Detached model state on render of context consumer if unmounted and context value does not change.

## [0.42.0] - 2022-12-02

### Added

- Ability to customize the `<head>` element of ReactPy's built-in client.
- `vdom_to_html` utility function.
- Ability to subscribe to changes that are made to mutable options.
- `del_html_head_body_transform` to remove `<html>`, `<head>`, and `<body>` while preserving children.
- Support for form element serialization

### Fixed

- `REACTPY_DEBUG_MODE` is now mutable and can be changed at runtime.
- Fix `html_to_vdom` improperly removing `<html>`, `<head>`, and `<body>` nodes.

### Removed

- Removed `reactpy.html.body` as it is currently unusable due to technological limitations.
- Removed `REACTPY_FEATURE_INDEX_AS_DEFAULT_KEY` option.
- Removed `serve_static_files` option from backend configuration.

### Deprecated

- `module_from_template`.

## [0.41.0] - 2022-11-01

### Changed

- The hooks `use_location` and `use_scope` are no longer implementation specific and are now available as top-level imports.
- Backend implementations now strip any URL prefix in the pathname for `use_location`.
- `use_state` now returns a named tuple with `value` and `set_value` fields.

### Added

- New `use_connection` hook which returns a `Connection` object containing `location`, `scope`, and `carrier`.

## [0.40.2] - 2022-09-13

### Changed

- Avoid the use of JSON patch for diffing models.

## [0.40.1] - 2022-09-11

### Fixed

- Child models after a component fail to render.

## [0.40.0] - 2022-08-13

### Fixed

- Fix edge cases where `html_to_vdom` can fail to convert HTML.
- Conditionally rendered components cannot use contexts.
- Use strict equality check for text, numeric, and binary types in hooks.
- Accidental mutation of old model causes invalid JSON Patch.

### Changed

- Set default timeout on Playwright page for testing.
- Track contexts in hooks as state.
- Remove non-standard `name` argument from `create_context`.

### Added

- `asgiref` as a dependency.
- `lxml` as a dependency.

## [0.39.0] - 2022-06-20

### Fixed

- `No module named 'reactpy.server'` from `reactpy.run`.
- Setting appropriate MIME type for web modules in `sanic` server implementation.

### Changed

- Renamed various: `reactpy.testing.server` to `reactpy.testing.backend`, `ServerFixture` to `BackendFixture`, `DisplayFixture.server` to `DisplayFixture.backend`.
- Removed `exports_default` parameter from `module_from_template`.

### Added

- Ability to specify versions with module templates (e.g. `module_from_template("react@^17.0.0", ...)`).

## [0.38.1] - 2022-04-15

### Fixed

- Missing file extension was causing a problem with WebPack.

## [0.38.0] - 2022-04-15

No changes.

## [0.37.2] - 2022-03-27

### Changed

- Renamed `proto` modules to `types` and added a top-level `reactpy.types` module.

### Fixed

- Fixed a typo that caused ReactPy to use the insecure `ws` web-socket protocol on pages loaded with `https` instead of the secure `wss` protocol.

## [0.37.1] - 2022-03-05

No changes.

## [0.37.0] - 2022-02-27

### Added

- Support for keys in HTML fragments.
- Use Context Hook.

### Fixed

- React warning about set state in unmounted component.
- Missing reset of schedule_render_later flag.

## [0.36.3] - 2022-02-18

### Fixed

- All child states wiped upon any child key change.
- Allow NoneType returns within components.

## [0.36.2] - 2022-02-02

### Fixed

- Hot fix for newly introduced `DeprecatedOption`.

## [0.36.1] - 2022-02-02

### Fixed

- Fix Key Error when Cleaning Up Event Handlers.
- Update Script Tag Behavior.

### Changed

- Renamed configuration option `REACTPY_WED_MODULES_DIR` to `REACTPY_WEB_MODULES_DIR`.

## [0.36.0] - 2022-01-30

### Added

- New `http.script` element which can behave similarly to a standard HTML `<script>` or, if no attributes are given, operate similarly to an effect.

### Fixed

- State mismatch during component update.
- Implement a script tag.

## [0.35.4] - 2022-01-27

### Fixed

- Keys for elements at the root of a component were not being tracked. Thus key changes for elements at the root did not trigger unmounts.

## [0.35.3] - 2022-01-27

### Changed

- Elements which changed type are now always deeply unmounted.

## [0.35.2] - 2022-01-26

### Fixed

- Allow children with the same key to vary in type.
- Client always looks for server at "/".
- Web modules get double file extensions with v0.35.x.

## [0.35.1] - 2022-01-18

### Fixed

- Re-add accidentally deleted `py.typed` file to distribution.

## [0.35.0] - 2022-01-18

### Added

- Default key for all elements and components is now their index amongst their siblings.
- `use_linked_inputs` widget.
- Starlette server implementation.

### Changed

- `REACTPY_FEATURE_INDEX_AS_DEFAULT_KEY` now defaults to `1`.

### Fixed

- Support Starlette Server.
- Fix unhandled case in module_from_template.
- Hide "Children" within REACTPY_DEBUG_MODE key warnings.
- Bug in Element Key Identity.
- Add iFrame to reactpy.html.
- React warning from module_from_template.

## [0.34.0] - 2021-12-16

### Changed

- Element value must now be accessed via `event['target']['value']` instead of `event['value']`.
- Added `event["currentTarget"]` and `event["relatedTarget"]` keys to the event dictionary.

### Fixed

- Move target attributes to `event['target']`.

## [0.33.3] - 2021-10-08

### Added

- Warning stating that `REACTPY_FEATURE_INDEX_AS_DEFAULT_KEY=1` will become the default in a future release.
- Ability to use the default export from a JavaScript module when calling `module_from_template` by specifying `exports_default=True`.

### Fixed

- Memory leak in SharedClientStateServer.
- Cannot use default export in react template.

## [0.33.2] - 2021-09-05

### Fixed

- Memory leak caused by event handlers that were not being removed when components updated.

## [0.33.1] - 2021-09-02

### Fixed

- Regression where the root element of the layout could not be updated.

## [0.33.0] - 2021-09-02

### Fixed

- Client-side error in mount-01d35dc3.js.
- Style cannot be updated.
- Displaying error messages in the client via `__error__` tag can leak secrets.
- Examples broken in docs.

### Changed

- Modified the Custom JavaScript Component interface to add a `create()` function to the `bind()` interface.

## [0.32.0] - 2021-08-20

### Changed

- Custom component interface now expects a single `bind()` function that returns an object with `render()` and `unmount()` functions.

### Fixed

- Docs broken on Firefox.
- URL resolution for web modules does not consider urls starting with /.
- Query params in package name for module_from_template not stripped.
- Search broken in docs.
- Move src/reactpy/client out of Python package.

## [0.31.0] - 2021-07-14

### Changed

- `Layout` is now a prototype and `Layout.update` is no longer a public API.
- Refactored the relationship between `LifeCycleHook` and `Layout`.
- `ComponentTypes` no longer needs a unique `id` attribute.

## [0.30.1] - 2021-07-13

### Fixed

- Warning if key is parameter of component render function.

## [0.30.0] - 2021-06-28

### Changed

- Removed all runtime reliance on NPM.
- `reactpy.client` is removed in favor of a stripped down `reactpy.web` module.
- `REACTPY_CLIENT_BUILD_DIR` config option is replaced with `REACTPY_WEB_MODULES_DIR`.

## [0.29.0] - 2021-06-20

### Changed

- Moved the runtime client build directory to a "user data" directory.
- Custom JS component interface has been reworked.

## [0.28.0] - 2021-06-01

### Added

- Support for `currentTime` attribute of audio/video elements.
- Support for the `files` attribute from the target of input elements.
- Model children are now passed to the JavaScript `mount()` function.
- `mountLayoutWithWebSocket` function to `@reactpy/client`.

### Changed

- Refactored existing server implementations as functions adhering to a protocol.
- Switched to a monorepo-style structure for JavaScript.
- Use a `loadImportSource()` function instead of trying to infer the path to dynamic modules.

## [0.27.0] - 2021-05-14

### Added

- `mount(element, component, props)` function which can be used to bind new elements to the DOM.

## [0.26.0] - 2021-05-07

### Fixed

- Fix for situations where a `Layout` can raise an error when a component whose state has been deleted is rendered.

## [0.25.0] - 2021-04-30

### Changed

- Refactored layout dispatcher by switching from a class-based approach to one that leverages pure functions.

## [0.24.0] - 2021-04-18

### Added

- Components and elements can now have "identity" - their state can be preserved across updates.
- `REACTPY_FEATURE_INDEX_AS_DEFAULT_KEY` feature flag.

## [0.23.1] - 2021-04-02

### Fixed

- Non-deterministic return order in install().

## [0.23.0] - 2021-04-01

### Added

- Changelog to docs.
- Automatically reconnect to server.
- Allow no reconnect in client.
- Cleaner way to specify import sources.
- FastAPI render server.

## [0.22.1] - 2021-01-02

### Fixed

- Fix missing find_available_port arg.

## [0.22.0] - 2020-12-24

### Fixed

- Fix doc build.
- Better server error capture in tests.
- Fix type annotations.
- Fix dark mode widget view.

### Changed

- Use Nox to run tests.
- Add .nox to gitignore.

## [0.21.0] - 2020-12-16

### Added

- Tornado render server.
- Render server documentation.

### Changed

- Renamed element to component.

## [0.20.1] - 2020-11-13

### Fixed

- Avoid sanic import.

## [0.20.0] - 2020-11-12

### Added

- Flask render server.

### Changed

- Moved idom_client_react into separate repo.
- Removed mountLayoutWithWebSocket.
- Removed more client implementation docs.

### Fixed

- Fix missing server event.

## [0.19.0] - 2020-10-19

### Fixed

- No cover last server error.

### Changed

- Refined test tooling.
- Added **all** to testing module.

## [0.18.1] - 2020-09-25

### Fixed

- Fix missing find_available_port arg.

## [0.18.0] - 2020-09-23

### Added

- Module components should be accessible as attrs.

### Fixed

- Fix doc import source URL.
- Minor JS fixes.
- Fix idom install.
- Better URL join logic in client.

### Changed

- Strip down test tooling.
- Avoid issues with bundlers.

## [0.17.1] - 2020-08-14

### Fixed

- Fix idom install.

## [0.17.0] - 2020-08-08

### Added

- Import source base URL with vdom fallback.

### Fixed

- Fix types.
- Fix mypy testing.

### Changed

- Bumped idom_client_react version.
- Use universal wheel.

## [0.16.0] - 2020-06-26

### Fixed

- Put setuptools_scm back in setup.py.
- Fix pyproject.toml.

### Changed

- Remove framework classifier.
- Only check last error in display context.
- Refactor and cleanup tests.
- Add public test tooling.

## [0.15.0] - 2020-05-02

### Added

- More docs.
- pyproject.toml support.

### Fixed

- Fix coverage.
- Fix misc bugs.
- Fix mypy.

### Changed

- Improve docs.
- Improve log messages.
- Rename config "item" to "entry".
- Upgrade snowpack to max possible.
- More tests for client management.

## [0.14.3] - 2020-04-10

### Fixed

- Fix JSON patch in-place (broke some components).
- Revert bad JSON patch usage.

## [0.14.2] - 2020-03-30

### Fixed

- Fix displayed version in docs.

## [0.14.1] - 2020-03-20

### Fixed

- Remove extra spaces in element children.

## [0.14.0] - 2020-03-20

### Added

- idom.run utility.

### Fixed

- Fix types.
- Fix doc examples.
- Simplify server constructor.

## [0.13.0] - 2020-02-15

### Added

- Well-defined client implementation layer.

### Fixed

- Fix types.
- Fix tests.

### Changed

- Remove ability to install modules at runtime via idom.Module.

## [0.12.0] - 2020-01-27

### Added

- Utility methods for LayoutUpdate (start, stop).
- useStateRef hook.

### Changed

- Move Jupyter out of base idom into idom-jupyter package.

## [0.11.3] - 2020-01-14

### Fixed

- Add utility method tests to LayoutUpdate.

## [0.11.2] - 2020-01-14

### Added

- Test dispatcher start and stop.

## [0.11.1] - 2019-12-20

### Changed

- Bump JS to 0.4.2.

## [0.11.0] - 2019-12-18

### Added

- MountLayout utility function.

### Fixed

- Fix issues.
- Correct package.json for idom-client-react.

### Changed

- Rename StateDispatcher to ViewDispatcher.
- Remove private=true from imports.
- Require anyio>=2.0.
- Rename static/ directory to app/.

## [0.10.4] - 2019-12-01

### Fixed

- Fix docs.

## [0.10.3] - 2019-12-01

### Fixed

- Publish package before docs.

## [0.10.2] - 2019-11-20

### Fixed

- Fix up tests.

### Added

- Material UI example.
- Concept of build cache.

## [0.10.1] - 2019-11-08

### Fixed

- Upgrade anyio (see https://github.com/agronholm/anyio/issues/155).

## [0.10.0] - 2019-11-07

### Added

- Fallbacks to imported JS in examples.

### Fixed

- Fix doc updates.
- Better URL join logic.

### Changed

- Removed async event handler.
- Renamed Renderer to Dispatcher.
- Removed AbstractElement.id.

## [0.9.2] - 2019-10-14

### Fixed

- Fix docs and improve doc example runner.

## [0.9.1] - 2019-10-10

### Fixed

- Add setuptools_scm as docs requirement.

## [0.9.0] - 2019-10-06

### Added

- Documentation for async effects.
- Fix effect cleanup timing.
- Test async effect.

### Fixed

- Fix layout test.
- Fix type annotations.

### Changed

- Element render functions don't need to be async.
- Dropped Python 3.6 support.

## [0.7.0] - 2020-08-09

### Added

- use_reducer hook.
- use_effect tests.
- Tests for use_ref and use_callback.
- HookCatcher utility.
- Layout tests.

### Fixed

- Fix bug in use_memo.
- Fix types for render and layout.
- Fix flake8 ignore doc examples.

### Changed

- Rename top level examples dir to notebooks.
- Remove unused test script.
- Effects run just before and after full render.
- Simplified rendering queue.
- Removed abstract layout (renamed to Layout.dispatch).

### Removed

- Drag-drop example.

## [0.6.0] - 2020-06-20

### Fixed

- Various bug fixes from early development.

### Added

- Core infrastructure for component rendering.

## [0.5.1] - 2019-10-24

### Fixed

- Fix tests and event handlers.

## [0.5.0] - 2019-06-13

### Added

- use_effect hook.
- Initial idom-jupyter support.
- Basic client-side rendering.
- createContext support.
- useCallback and useMemo.
- Initial testing infrastructure.

### Fixed

- Fix various rendering and state management bugs.

### Removed

- Legacy state management.

## [0.4.2] - 2019-03-20

### Fixed

- Revert "make vdom a simple dict".

## [0.4.1] - 2019-02-26

### Fixed

- Fix tests.

## [0.4.0] - 2019-02-02

### Added

- Core functionality for idom.

### Changed

- Restructure around idom-core and idom-legacy.

## [0.3.0] - 2018-12-18

### Added

- Core functionality with hooks (useState, useEffect, etc.).

### Fixed

- Fix initial rendering issues.

## [0.2.0] - 2018-10-22

### Added

- Basic functionality.

### Fixed

- Initial bug fixes.

## [0.1.2] - 2018-08-03

### Fixed

- Fix import issues.

## [0.1.0] - 2018-07-30

### Added

- Initial release.

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
[0.23.0]: https://github.com/reactive-python/reactpy/compare/0.22.1...0.23.0
[0.22.1]: https://github.com/reactive-python/reactpy/compare/0.22.0...0.22.1
[0.22.0]: https://github.com/reactive-python/reactpy/compare/0.21.0...0.22.0
[0.21.0]: https://github.com/reactive-python/reactpy/compare/0.20.1...0.21.0
[0.20.1]: https://github.com/reactive-python/reactpy/compare/0.20.0...0.20.1
[0.20.0]: https://github.com/reactive-python/reactpy/compare/0.19.0...0.20.0
[0.19.0]: https://github.com/reactive-python/reactpy/compare/0.18.1...0.19.0
[0.18.1]: https://github.com/reactive-python/reactpy/compare/0.18.0...0.18.1
[0.18.0]: https://github.com/reactive-python/reactpy/compare/0.17.1...0.18.0
[0.17.1]: https://github.com/reactive-python/reactpy/compare/0.17.0...0.17.1
[0.17.0]: https://github.com/reactive-python/reactpy/compare/0.16.0...0.17.0
[0.16.0]: https://github.com/reactive-python/reactpy/compare/0.15.0...0.16.0
[0.15.0]: https://github.com/reactive-python/reactpy/compare/0.14.3...0.15.0
[0.14.3]: https://github.com/reactive-python/reactpy/compare/0.14.2...0.14.3
[0.14.2]: https://github.com/reactive-python/reactpy/compare/0.14.1...0.14.2
[0.14.1]: https://github.com/reactive-python/reactpy/compare/0.14.0...0.14.1
[0.14.0]: https://github.com/reactive-python/reactpy/compare/0.13.0...0.14.0
[0.13.0]: https://github.com/reactive-python/reactpy/compare/0.12.0...0.13.0
[0.12.0]: https://github.com/reactive-python/reactpy/compare/0.11.3...0.12.0
[0.11.3]: https://github.com/reactive-python/reactpy/compare/0.11.2...0.11.3
[0.11.2]: https://github.com/reactive-python/reactpy/compare/0.11.1...0.11.2
[0.11.1]: https://github.com/reactive-python/reactpy/compare/0.11.0...0.11.1
[0.11.0]: https://github.com/reactive-python/reactpy/compare/0.10.4...0.11.0
[0.10.4]: https://github.com/reactive-python/reactpy/compare/0.10.3...0.10.4
[0.10.3]: https://github.com/reactive-python/reactpy/compare/0.10.2...0.10.3
[0.10.2]: https://github.com/reactive-python/reactpy/compare/0.10.1...0.10.2
[0.10.1]: https://github.com/reactive-python/reactpy/compare/0.10.0...0.10.1
[0.10.0]: https://github.com/reactive-python/reactpy/compare/0.9.2...0.10.0
[0.9.2]: https://github.com/reactive-python/reactpy/compare/0.9.1...0.9.2
[0.9.1]: https://github.com/reactive-python/reactpy/compare/0.9.0...0.9.1
[0.9.0]: https://github.com/reactive-python/reactpy/compare/0.7.0...0.9.0
[0.7.0]: https://github.com/reactive-python/reactpy/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/reactive-python/reactpy/compare/0.5.1...0.6.0
[0.5.1]: https://github.com/reactive-python/reactpy/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/reactive-python/reactpy/compare/0.4.2...0.5.0
[0.4.2]: https://github.com/reactive-python/reactpy/compare/0.4.1...0.4.2
[0.4.1]: https://github.com/reactive-python/reactpy/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/reactive-python/reactpy/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/reactive-python/reactpy/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/reactive-python/reactpy/compare/0.1.2...0.2.0
[0.1.2]: https://github.com/reactive-python/reactpy/compare/0.1.0...0.1.2
[0.1.0]: https://github.com/reactive-python/reactpy/releases/tag/0.1.0
