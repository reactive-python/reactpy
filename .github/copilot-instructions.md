# ReactPy Development Instructions

ReactPy is a Python library for building user interfaces without JavaScript. It creates React-like components that render to web pages using a Python-to-JavaScript bridge.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

**Prerequisites:**
- Install Python 3.9+ from https://www.python.org/downloads/
- Install Hatch: `pip install hatch`
- Install Bun JavaScript runtime: `curl -fsSL https://bun.sh/install | bash && source ~/.bashrc`
- Install Git

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
- `hatch run javascript:build` -- takes 15 seconds. NEVER CANCEL. Set timeout to 60+ minutes for safety.
- This builds three packages: event-to-object, @reactpy/client, and @reactpy/app

**Build Python Package:**
- `hatch build --clean` -- takes 10 seconds. NEVER CANCEL. Set timeout to 60+ minutes for safety.

**Run Python Tests:**
- `hatch test` -- takes 10-30 seconds for basic tests. NEVER CANCEL. Set timeout to 60+ minutes for full test suite.
- `hatch test -k test_name` -- run specific tests
- `hatch test tests/test_config.py` -- run specific test files
- Note: Some tests require Playwright browser automation and may fail in headless environments

**Run Python Linting and Formatting:**
- `hatch fmt` -- Run all linters and formatters (~1 second)
- `hatch fmt --check` -- Check formatting without making changes (~1 second)
- `hatch fmt --linter` -- Run only linters
- `hatch fmt --formatter` -- Run only formatters
- `hatch run python:type_check` -- Run Python type checker (~10 seconds)

**Run JavaScript Tasks:**
- `hatch run javascript:check` -- Lint and type-check JavaScript (10 seconds). NEVER CANCEL. Set timeout to 30+ minutes.
- `hatch run javascript:fix` -- Format JavaScript code
- `hatch run javascript:test` -- Run JavaScript tests (note: may fail in headless environments due to DOM dependencies)

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
- `hatch fmt --check` -- Ensure code is properly formatted
- `hatch run python:type_check` -- Ensure no type errors  
- `hatch run javascript:check` -- Ensure JavaScript passes linting
- Test basic component creation and rendering as shown above
- Test server creation if working on server-related features

**Integration Testing:**
- ReactPy can be deployed with FastAPI, Flask, Sanic, Tornado via ASGI
- For browser testing, Playwright is used but requires additional setup
- Test component VDOM rendering directly when browser testing isn't available
- Validate that JavaScript builds are included in Python package after changes

## Repository Structure

### Key Directories:
- `src/reactpy/` -- Main Python package source code
- `src/js/` -- JavaScript packages that get bundled with Python
- `src/build_scripts/` -- Build automation scripts
- `tests/` -- Python test suite
- `docs/` -- Documentation source (currently transitioning to MkDocs)

### Important Files:
- `pyproject.toml` -- Python project configuration and build scripts
- `src/js/package.json` -- JavaScript development dependencies
- `src/js/packages/` -- Individual JavaScript packages
- `tests/conftest.py` -- Test configuration and fixtures

### Key Components:
- `src/reactpy/core/` -- Core ReactPy functionality (components, hooks, VDOM)
- `src/reactpy/web/` -- Web module management and exports
- `src/reactpy/widgets/` -- Built-in UI components
- `src/reactpy/pyscript/` -- PyScript integration
- `src/reactpy/_html.py` -- HTML element factory functions

## Common Tasks

### Build Time Expectations:
- JavaScript build: 15 seconds
- Python package build: 10 seconds  
- Python linting: 1 second
- JavaScript linting: 10 seconds
- Type checking: 10 seconds
- Full CI pipeline: 5-10 minutes

### Development Workflow:
1. Make code changes
2. Run `hatch fmt` to format code (~1 second)
3. Run `hatch run python:type_check` for type checking (~10 seconds)
4. Run `hatch run javascript:check` if JavaScript was modified (~10 seconds)
5. Run relevant tests with `hatch test`
6. Validate component functionality manually using validation tests above

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
- JavaScript packages are in `src/js/packages/`
- Three main packages: event-to-object, @reactpy/client, @reactpy/app
- Built JavaScript gets bundled into `src/reactpy/static/`
- Always rebuild JavaScript after changes: `hatch run javascript:build`

## Troubleshooting

### Build Issues:
- If JavaScript build fails, try: `hatch run "src/build_scripts/clean_js_dir.py"` then rebuild
- If Python build fails, ensure all dependencies in pyproject.toml are available
- Network timeouts during pip install are common in CI environments
- Missing dependencies error: Install ASGI dependencies with `pip install orjson asgiref asgi-tools servestatic`

### Test Issues:
- Playwright tests may fail in headless environments -- this is expected
- Tests requiring browser DOM should be marked appropriately  
- Use `hatch test -k "not playwright"` to skip browser-dependent tests
- JavaScript tests may fail with "window is not defined" in Node.js environment -- this is expected

### Import Issues:
- ReactPy must be installed or src/ must be in Python path
- Main imports: `from reactpy import component, html, use_state`
- Server imports: `from reactpy.executors.asgi.standalone import ReactPy`
- Web functionality: `from reactpy.web import export, module_from_url`

### Server Issues:
- Missing ASGI dependencies: Install with `pip install orjson asgiref asgi-tools servestatic uvicorn`
- For FastAPI integration: `pip install fastapi uvicorn`
- For Flask integration: `pip install flask` (requires additional backend package)
- For development servers, use ReactPy ASGI standalone for simplest setup

## CI/CD Information

The repository uses GitHub Actions with these key jobs:
- `test-python-coverage` -- Python test coverage
- `lint-python` -- Python linting and type checking
- `test-python` -- Cross-platform Python testing
- `lint-javascript` -- JavaScript linting and type checking

The CI workflow is defined in `.github/workflows/check.yml` and uses the reusable workflow in `.github/workflows/.hatch-run.yml`.

Always ensure your changes pass local validation before pushing, as the CI pipeline will run the same checks.