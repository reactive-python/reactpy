## Overview

<p class="intro" markdown>

There are two test suites in this project, and they live in different places. The Python and JavaScript suites exercise ReactPy itself and run through `hatch`; the documentation checks exercise the pages you are reading and run through `mkdocs`. Knowing which one a failing command belongs to is most of debugging it.

</p>

!!! summary "You will learn"

    -   How to run the Python test suite, and why it needs a browser installed
    -   How to run the documentation build checks that gate every docs pull request
    -   Which command failures are yours and which are environmental

!!! abstract "Note"

    The ReactPy package and its `tests/` directory live on the [`main`](https://github.com/reactive-python/reactpy) branch. This documentation site is authored on the [`new-docs`](https://github.com/reactive-python/reactpy/tree/new-docs) branch, which contains only `docs/` — running a test command there collects zero tests rather than failing, which reads like a pass and is not one. If `hatch test` reports `no tests ran`, you are on the wrong branch, not on a clean tree.

## Prerequisites

The development environment is managed by [Hatch](https://hatch.pypa.io/latest/), which creates and maintains its own virtual environments. Install Hatch, then clone:

```bash
git clone https://github.com/reactive-python/reactpy.git
cd reactpy
```

You also need [Bun](https://bun.sh/) for the JavaScript packages. Python must be 3.11 or newer — `requires-python` in `pyproject.toml` is `>=3.11`, and the test matrix runs 3.11 through 3.14.

!!! warning "Pitfall"

    Do not install the project's dependencies with `pip install -r` into your own environment. Hatch owns those environments, and a hand-built one drifts from CI in ways that look like your fault. The one exception is the documentation requirements, which are installed separately below.

## Python tests

The suite is `pytest`-based and runs under Hatch:

```bash
hatch test                                    # current Python version
hatch test --all                              # every version in the matrix
hatch test -k test_use_connection             # a single test by name
```

CI runs `hatch test --parallel --retries 10` across three operating systems and four Python versions, and a separate coverage job runs `hatch test --parallel --cover --retries 10`.

The suite needs a browser. Each test run installs Playwright's Chromium, builds the JavaScript client, and builds a wheel before it invokes `pytest` — that is what the `hatch-test` environment's `run` script does. A first run is therefore slow, and a failure inside Chromium installation looks identical to a failure in the test itself. Read the top of the output, not the bottom.

```bash
playwright install chromium
playwright install-deps chromium   # optional; fails harmlessly on some systems
```

Tests are session-scoped around one browser and one backend server, defined in `tests/conftest.py`, and that file also turns on `REACTPY_DEBUG` and `REACTPY_ASYNC_RENDERING` for the whole session. Two consequences:

-   A test that passes alone and fails in the suite may be reading state a previous test left behind. Reproduce with `-k` before you chase it.
-   Because debug mode is on in tests and off by default in production, some errors surface only in the suite. Debug-mode checks such as `REACTPY_CHECK_VDOM_SPEC` are exactly this.

Configuration lives under `[tool.pytest.ini_options]` in `pyproject.toml`: `--strict-config`, `--strict-markers`, `xfail_strict`, `asyncio_mode = "auto"`, `testpaths = "tests"`, and a 120-second per-test timeout. `xfail_strict` means an expected failure that unexpectedly passes is itself a failure, so an xfail you fixed must be deleted rather than left alone.

### What the helpers are for

`reactpy.testing` exists because a UI is only correct once it renders in a browser. The acceptance bar is that the real artefact behaves, not that a function returned the expected shape.

-   `DisplayFixture` — serves a component and gives you a Playwright `page` to drive it: `await display.show(my_component)`, then `display.page`.
-   `BackendFixture` — the server side, usually paired with `DisplayFixture` as in `conftest.py`.
-   `poll(...)` — retries a condition until it holds or the timeout expires. Use it instead of `asyncio.sleep`, which passes vacuously on a slow machine and flakes on a fast one.
-   `HookCatcher` and `StaticEventHandler` — capture a component's life-cycle hook and an event handler's target, for delivering events without a click.
-   `capture_reactpy_logs`, `assert_reactpy_did_log`, `assert_reactpy_did_not_log` — assert on server-side log output, which is where ReactPy puts swallowed handler and effect errors.

`conftest.py` also installs an autouse fixture that fails a test if any ReactPy log record carries an exception. That is deliberate: an error logged server-side while the browser stays quiet is the most common way a ReactPy bug hides. If a new test trips it, the exception is real even when the assertion you wrote passes.

## JavaScript tests

The client packages are tested with Bun:

```bash
hatch run javascript:test     # run the JavaScript tests
hatch run javascript:check    # lint and format check
hatch run javascript:fix      # lint and write fixes to disk
hatch run javascript:build    # rebuild the client bundles
```

Changes under `src/js/` need a rebuild before Python tests can see them. The test script does this itself, but a manual run against a stale bundle will not reflect your edit.

## Linting and type checking

```bash
hatch fmt                     # format and lint, writing fixes
hatch fmt --check             # the CI form: report, do not write
hatch run python:type_check   # pyright over src/reactpy
```

CI runs `hatch fmt src/reactpy --check` followed by `hatch run python:type_check`.

!!! warning "Pitfall"

    Run `hatch fmt --check` before you commit, not `hatch fmt`. Bare `hatch fmt` rewrites files, so a run that "passes" has already edited your working tree — including files you did not intend to touch. Scope it (`hatch fmt docs/`) if you only want part of the tree.

Formatting is Ruff at a line length of 88. The rules that bite most in this repository are set in `pyproject.toml`; `docs/**/*.py` already ignores `E402`, `S102`, `T201`, `TID252`, `RUF059`, and `INP001`, because example files are teaching snippets rather than importable modules.

## Documentation checks

These are the gates a documentation pull request must clear. Run them from the repository root.

```bash
hatch fmt --check docs/             # formatting and lint
cd docs && mkdocs build --strict    # build, fail on warnings
```

Plus the type check over the example files, which are real Python:

```bash
pyright --pythonpath <your-env>/bin/python docs/
```

`mkdocs build --strict` is the important one: it turns broken internal links, unresolvable includes, and pages missing from `nav:` into build failures. But the examples in `docs/examples/` are the source of truth for every snippet on the site, and a snippet that does not *run* is a docs bug the build will not catch on its own. That part is on you.

!!! warning "Pitfall"

    Do not judge a build by its log output alone. A grep-style check on the output hides a nonzero exit:

    ```bash
    cd docs && mkdocs build --strict; echo "exit=$?"
    ```

    In a bash pipeline, use `echo "${PIPESTATUS[0]}"` instead — a trailing `| grep` that finds a match makes the pipeline's exit code meaningless.

## Running the site locally

```bash
pip install -r docs/requirements.txt
cd docs && mkdocs serve
```

Then follow the printed URL. Editing any file under `docs/src/` or `docs/examples/` reloads the page.

The requirements file pins `mkdocs-material==9.4.0`, which transitively pins `regex==2022.10.31`. That release ships wheels only through CPython 3.11, so on 3.12 and newer the install falls back to a source build and fails without a C compiler. If the docs install dies inside `regex`, use Python 3.11 or install a newer `mkdocs-material` — nothing in these pages depends on the pin.

## Checking your work

Before calling anything done, run the gates in this order and read every failure:

1.  `hatch fmt --check docs/` — formatting and lint
2.  `pyright docs/` — types in the examples
3.  `cd docs && mkdocs build --strict` — links, includes, nav
4.  The relevant tests, for code changes
5.  The real user scenario, by hand — open the page, click the control

Steps 1–4 can all pass while the thing you built does not work. A status is not an acceptance test: run the artefact. For a docs example that means mounting it in a browser and confirming the DOM changed, because a ReactPy component can render, error server-side, and show a blank region while the HTTP response still reads 200.

!!! info "Deep Dive"

    Two harness traps have made broken examples look green more than once. First, the decorated function is a constructor: `counter` itself has no `.render()` and `Layout(counter)` raises `TypeError: Expected a ReactPy component`, so you must pass an instance. The instance *does* have `.render()`, but calling it outside a `Layout` raises `RuntimeError: No life cycle hook is active. Are you rendering in a layout?` for any component that uses a hook — which silently skips the behaviour you meant to test. Render through `async with Layout(counter()) as layout: await layout.render()`. Second, ReactPy formats exception text into the model only when `REACTPY_DEBUG` is on; with it off, a component that raised renders as `{"tagName": "", "error": ""}` — an empty region and no message. Set the variable when you are probing failures, and unset it when you are checking what a user would actually see.

## Recap

-   Two suites: `hatch test` for ReactPy (on `main`), `mkdocs build --strict` for the docs.
-   `hatch test` reporting `no tests ran` means the suite is not there, not that it passed.
-   Python tests need Playwright's Chromium and build a wheel before `pytest` starts.
-   `conftest.py` forces debug mode and fails any test that logs an exception.
-   Run `hatch fmt --check`, never bare `hatch fmt`, before committing.
-   Check exit codes, not log text; then verify the real behaviour by hand.

## Related

-   [Contributing Code](./code.md) — branches, commits, and the pull request checklist
-   [Contributing Documentation](./docs.md) — page conventions and the example-file workflow
-   [Changelog](./changelog.md) — when a change needs an entry
