# ReactPy Development Instructions

ReactPy is a Python library for building user interfaces without JavaScript. It creates React-like components that render to web pages using a Python-to-JavaScript bridge.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

**IMPORTANT**: This package uses modern Python tooling with Hatch for all development workflows. Always use Hatch commands for development tasks.

**BUG INVESTIGATION**: When investigating whether a bug was already resolved in a previous version, always prioritize searching through `docs/source/about/changelog.rst` first before using Git history. Only search through Git history when no relevant changelog entries are found.

## Working Effectively

### Bootstrap, Build, and Test the Repository

**Prerequisites:**

-   Install Python 3.9+ from https://www.python.org/downloads/
-   Install Hatch: `pip install hatch`
-   Install Bun JavaScript runtime: `curl -fsSL https://bun.sh/install | bash && source ~/.bashrc`
-   Install Git

**Initial Setup:**

```bash
git clone https://github.com/reactive-python/reactpy.git
cd reactpy
```

**Install Dependencies for Development:**

```bash
# Install core ReactPy dependencies
pip install fastjsonschema requests lxml anyio typing-extensions

# Install ASGI dependencies for server functionality
pip install orjson asgiref asgi-tools servestatic uvicorn fastapi

# Optional: Install additional servers
pip install flask sanic tornado
```

**Build JavaScript Packages:**

-   `hatch run javascript:build` -- takes 15 seconds. NEVER CANCEL. Set timeout to 60+ minutes for safety.
-   This builds three packages: event-to-object, @reactpy/client, and @reactpy/app

**Build Python Package:**

-   `hatch build --clean` -- takes 10 seconds. NEVER CANCEL. Set timeout to 60+ minutes for safety.

**Run Python Tests:**

-   `hatch test --parallel` -- takes 10-30 seconds for basic tests. NEVER CANCEL. Set timeout to 2 minutes for full test suite. **All tests must always pass - failures are never expected or allowed.**
-   `hatch test --parallel --cover` -- run tests with coverage reporting (used in CI)
-   `hatch test --parallel -k test_name` -- run specific tests
-   `hatch test --parallel tests/test_config.py` -- run specific test files

**Run Python Linting and Formatting:**

-   `hatch fmt` -- Run all linters and formatters (~1 second)
-   `hatch fmt --check` -- Check formatting without making changes (~1 second)
-   `hatch fmt --linter` -- Run only linters
-   `hatch fmt --formatter` -- Run only formatters
-   `hatch run python:type_check` -- Run Python type checker (~10 seconds)

**Run JavaScript Tasks:**

-   `hatch run javascript:check` -- Lint and type-check JavaScript (10 seconds). NEVER CANCEL. Set timeout to 30+ minutes.
-   `hatch run javascript:fix` -- Format JavaScript code
-   `hatch run javascript:test` -- Run JavaScript tests

**Interactive Development Shell:**

-   `hatch shell` -- Enter an interactive shell environment with all dependencies installed
-   `hatch shell default` -- Enter the default development environment
-   Use the shell for interactive debugging and development tasks

## Validation

Always manually validate any new code changes through these steps:

**Basic Functionality Test:**

```python
# Add src to path if not installed
import sys, os
sys.path.insert(0, os.path.join("/path/to/reactpy", "src"))

# Test that imports and basic components work
import reactpy
from reactpy import component, html, use_state

@component
def test_component():
    return html.div([
        html.h1("Test"),
        html.p("ReactPy is working")
    ])

# Verify component renders
vdom = test_component()
print(f"Component rendered: {type(vdom)}")
```

**Server Functionality Test:**

```python
# Test ASGI server creation (most common deployment)
from reactpy import component, html
from reactpy.executors.asgi.standalone import ReactPy
import uvicorn

@component
def hello_world():
    return html.div([
        html.h1("Hello, ReactPy!"),
        html.p("Server is working!")
    ])

# Create ASGI app (don't run to avoid hanging)
app = ReactPy(hello_world)
print("✓ ASGI server created successfully")

# To actually run: uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Hooks and State Test:**

```python
from reactpy import component, html, use_state

@component
def counter_component(initial=0):
    count, set_count = use_state(initial)

    return html.div([
        html.h1(f"Count: {count}"),
        html.button({
            "onClick": lambda event: set_count(count + 1)
        }, "Increment")
    ])

# Test component with hooks
counter = counter_component(5)
print(f"✓ Hook-based component: {type(counter)}")
```

**Always run these validation steps before completing work:**

-   `hatch fmt --check` -- Ensure code is properly formatted (never expected to fail)
-   `hatch run python:type_check` -- Ensure no type errors (never expected to fail)
-   `hatch run javascript:check` -- Ensure JavaScript passes linting (never expected to fail)
-   Test basic component creation and rendering as shown above
-   Test server creation if working on server-related features
-   Run relevant tests with `hatch test --parallel` -- **All tests must always pass - failures are never expected or allowed**

**Integration Testing:**

-   ReactPy can be deployed with FastAPI, Flask, Sanic, Tornado via ASGI
-   For browser testing, Playwright is used but requires additional setup
-   Test component VDOM rendering directly when browser testing isn't available
-   Validate that JavaScript builds are included in Python package after changes

## Repository Structure and Navigation

### Key Directories:

-   `src/reactpy/` -- Main Python package source code
    -   `core/` -- Core ReactPy functionality (components, hooks, VDOM)
    -   `web/` -- Web module management and exports
    -   `executors/` -- Server integration modules (ASGI, etc.)
    -   `testing/` -- Testing utilities and fixtures
    -   `pyscript/` -- PyScript integration
    -   `static/` -- Bundled JavaScript files
    -   `_html.py` -- HTML element factory functions
-   `src/js/` -- JavaScript packages that get bundled with Python
    -   `packages/event-to-object/` -- Event serialization package
    -   `packages/@reactpy/client/` -- Client-side React integration
    -   `packages/@reactpy/app/` -- Application framework
-   `src/build_scripts/` -- Build automation scripts
-   `tests/` -- Python test suite with comprehensive coverage
-   `docs/` -- Documentation source (MkDocs-based, transitioning setup)

### Important Files:

-   `pyproject.toml` -- Python project configuration and Hatch environments
-   `src/js/package.json` -- JavaScript development dependencies
-   `tests/conftest.py` -- Test configuration and fixtures
-   `docs/source/about/changelog.rst` -- Version history and changes
-   `.github/workflows/check.yml` -- CI/CD pipeline configuration

## Common Tasks

### Build Time Expectations:

-   JavaScript build: 15 seconds
-   Python package build: 10 seconds
-   Python linting: 1 second
-   JavaScript linting: 10 seconds
-   Type checking: 10 seconds
-   Full CI pipeline: 5-10 minutes

### Running ReactPy Applications:

**ASGI Standalone (Recommended):**

```python
from reactpy import component, html
from reactpy.executors.asgi.standalone import ReactPy
import uvicorn

@component
def my_app():
    return html.h1("Hello World")

app = ReactPy(my_app)
uvicorn.run(app, host="127.0.0.1", port=8000)
```

**With FastAPI:**

```python
from fastapi import FastAPI
from reactpy import component, html
from reactpy.executors.asgi.middleware import ReactPyMiddleware

@component
def my_component():
    return html.h1("Hello from ReactPy!")

app = FastAPI()
app.add_middleware(ReactPyMiddleware, component=my_component)
```

### Creating Components:

```python
from reactpy import component, html, use_state

@component
def my_component(initial_value=0):
    count, set_count = use_state(initial_value)

    return html.div([
        html.h1(f"Count: {count}"),
        html.button({
            "onClick": lambda event: set_count(count + 1)
        }, "Increment")
    ])
```

### Working with JavaScript:

-   JavaScript packages are in `src/js/packages/`
-   Three main packages: event-to-object, @reactpy/client, @reactpy/app
-   Built JavaScript gets bundled into `src/reactpy/static/`
-   Always rebuild JavaScript after changes: `hatch run javascript:build`

## Common Hatch Commands

The following are key commands for daily development:

### Development Commands

```bash
hatch test --parallel                          # Run all tests (**All tests must always pass**)
hatch test --parallel --cover                  # Run tests with coverage (used in CI)
hatch test --parallel -k test_name             # Run specific tests
hatch fmt                           # Format code with all formatters
hatch fmt --check                   # Check formatting without changes
hatch run python:type_check         # Run Python type checker
hatch run javascript:build          # Build JavaScript packages (15 seconds)
hatch run javascript:check          # Lint JavaScript code (10 seconds)
hatch run javascript:fix            # Format JavaScript code
hatch build --clean                 # Build Python package (10 seconds)
```

### Environment Management

```bash
hatch env show                      # Show all environments
hatch shell                         # Enter default shell
hatch shell default                 # Enter development shell
```

### Build Timing Expectations

-   **NEVER CANCEL**: All commands complete within 60 seconds in normal operation
-   **JavaScript build**: 15 seconds (hatch run javascript:build)
-   **Python package build**: 10 seconds (hatch build --clean)
-   **Python linting**: 1 second (hatch fmt)
-   **JavaScript linting**: 10 seconds (hatch run javascript:check)
-   **Type checking**: 10 seconds (hatch run python:type_check)
-   **Unit tests**: 10-30 seconds (varies by test selection)
-   **Full CI pipeline**: 5-10 minutes

## Development Workflow

Follow this step-by-step process for effective development:

1. **Bootstrap environment**: Ensure you have Python 3.9+ and run `pip install hatch`
2. **Make your changes** to the codebase
3. **Run formatting**: `hatch fmt` to format code (~1 second)
4. **Run type checking**: `hatch run python:type_check` for type checking (~10 seconds)
5. **Run JavaScript linting** (if JavaScript was modified): `hatch run javascript:check` (~10 seconds)
6. **Run relevant tests**: `hatch test --parallel` with specific test selection if needed. **All tests must always pass - failures are never expected or allowed.**
7. **Validate component functionality** manually using validation tests above
8. **Build JavaScript** (if modified): `hatch run javascript:build` (~15 seconds)
9. **Update documentation** when making changes to Python source code (required)
10. **Add changelog entry** for all significant changes to `docs/source/about/changelog.rst`

**IMPORTANT**: Documentation must be updated whenever changes are made to Python source code. This is enforced as part of the development workflow.

**IMPORTANT**: Significant changes must always include a changelog entry in `docs/source/about/changelog.rst` under the appropriate version section.

## Troubleshooting

### Build Issues:

-   If JavaScript build fails, try: `hatch run "src/build_scripts/clean_js_dir.py"` then rebuild
-   If Python build fails, ensure all dependencies in pyproject.toml are available
-   Network timeouts during pip install are common in CI environments
-   Missing dependencies error: Install ASGI dependencies with `pip install orjson asgiref asgi-tools servestatic`

### Import Issues:

-   ReactPy must be installed or src/ must be in Python path
-   Main imports: `from reactpy import component, html, use_state`
-   Server imports: `from reactpy.executors.asgi.standalone import ReactPy`
-   Web functionality: `from reactpy.web import export, module_from_url`

### Server Issues:

-   Missing ASGI dependencies: Install with `pip install orjson asgiref asgi-tools servestatic uvicorn`
-   For FastAPI integration: `pip install fastapi uvicorn`
-   For Flask integration: `pip install flask` (requires additional backend package)
-   For development servers, use ReactPy ASGI standalone for simplest setup

## Package Dependencies

Modern dependency management via pyproject.toml:

**Core Runtime Dependencies:**

-   `fastjsonschema >=2.14.5` -- JSON schema validation
-   `requests >=2` -- HTTP client library
-   `lxml >=4` -- XML/HTML processing
-   `anyio >=3` -- Async I/O abstraction
-   `typing-extensions >=3.10` -- Type hints backport

**Optional Dependencies (install via extras):**

-   `asgi` -- ASGI server support: `orjson`, `asgiref`, `asgi-tools`, `servestatic`, `pip`
-   `jinja` -- Template integration: `jinja2-simple-tags`, `jinja2 >=3`
-   `uvicorn` -- ASGI server: `uvicorn[standard]`
-   `testing` -- Browser automation: `playwright`
-   `all` -- All optional dependencies combined

**Development Dependencies (managed by Hatch):**

-   **JavaScript tooling**: Bun runtime for building packages
-   **Python tooling**: Hatch environments handle all dev dependencies automatically

## CI/CD Information

The repository uses GitHub Actions with these key jobs:

-   `test-python-coverage` -- Python test coverage with `hatch test --parallel --cover`
-   `lint-python` -- Python linting and type checking via `hatch fmt --check` and `hatch run python:type_check`
-   `test-python` -- Cross-platform Python testing across Python 3.10-3.13 and Ubuntu/macOS/Windows
-   `lint-javascript` -- JavaScript linting and type checking

The CI workflow is defined in `.github/workflows/check.yml` and uses the reusable workflow in `.github/workflows/.hatch-run.yml`.

**Build Matrix:**

-   **Python versions**: 3.10, 3.11, 3.12, 3.13
-   **Operating systems**: Ubuntu, macOS, Windows
-   **Test execution**: Hatch-managed environments ensure consistency across platforms

Always ensure your changes pass local validation before pushing, as the CI pipeline will run the same checks.

## Important Notes

-   **This is a Python-to-JavaScript bridge library**, not a traditional web framework - it enables React-like components in Python
-   **Component rendering uses VDOM** - components return virtual DOM objects that get serialized to JavaScript
-   **All builds and tests run quickly** - if something takes more than 60 seconds, investigate the issue
-   **Hatch environments provide full isolation** - no need to manage virtual environments manually
-   **JavaScript packages are bundled into Python** - the build process combines JS and Python into a single distribution
-   **Documentation updates are required** when making changes to Python source code
-   **Always update this file** when making changes to the development workflow, build process, or repository structure
-   **All tests must always pass** - failures are never expected or allowed in a healthy development environment
