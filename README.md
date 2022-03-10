# IDOM &middot; [![Tests](https://github.com/idom-team/idom/workflows/Test/badge.svg?event=push)](https://github.com/idom-team/idom/actions?query=workflow%3ATest) [![PyPI Version](https://img.shields.io/pypi/v/idom.svg)](https://pypi.python.org/pypi/idom) [![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://github.com/idom-team/idom/blob/main/LICENSE)

IDOM is a Python framework for building **interactive websites without needing a single line of JavaScript**. Web elements you provide (ex. `button`, `div`, `image`) are combined into reusable "components". Components [can be nested together](https://idom-docs.herokuapp.com/docs/guides/creating-interfaces/your-first-components/index.html#conditional-rendering) and utilize [ReactJS-style hooks](https://idom-docs.herokuapp.com/docs/reference/hooks-api.html) to create complex web pages. Ultimately, all IDOM components are sent to the browser and are rendered by ReactJS.

When needed, you can import JavaScript from [NPM](https://idom-docs.herokuapp.com/docs/guides/escape-hatches/javascript-components.html#dynamically-loaded-components) into your Python components. If you want to develop a component entirely within JavaScript, you can utilize the [JavaScript Components API](https://idom-docs.herokuapp.com/docs/guides/escape-hatches/javascript-components.html#custom-javascript-components) for additional flexibility.

Due to our ecosystem independent design, IDOM can be added to existing projects built on a variety of sync and async web frameworks. For example, you can take components originally developed in Jupyter and embed them into an existing Flask application.

Currently supported web frameworks include: `FastAPI`, `Flask`, `Sanic`, `Tornado`, `Django`, `Plotly-Dash`, and `Jupyter`.

# At a Glance

To get a rough idea of how to write apps in IDOM, take a look at this tiny _Hello World_ application.

```python
from idom import component, html, run

@component
def App():
    return html.h1("Hello, World!")

run(App)
```

# Resources

Follow the links below to find out more about this project.

-   [Try it Now](https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out IDOM in a Jupyter Notebook.
-   [Documentation](https://idom-docs.herokuapp.com/) - learn how to install, run, and use IDOM.
-   [Community Forum](https://github.com/idom-team/idom/discussions) - ask questions, share ideas, and show off projects.
-   [Contributor Guide](https://idom-docs.herokuapp.com/docs/developing-idom/contributor-guide.html) - see how you can help develop this project.
-   [Code of Conduct](https://github.com/idom-team/idom/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.
