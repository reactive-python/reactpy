# ReactPy &middot; [![Tests](https://github.com/reactive-python/reactpy/workflows/test/badge.svg)](https://github.com/reactive-python/reactpy/actions?query=workflow%3ATest) [![PyPI Version](https://img.shields.io/pypi/v/reactpy.svg)](https://pypi.python.org/pypi/reactpy) [![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://github.com/reactive-python/reactpy/blob/main/LICENSE)

ReactPy connects your Python web framework of choice to a ReactJS frontend, allowing you to create **interactive websites without needing JavaScript!**

Following ReactJS styling, web elements are combined into [reusable "components"](https://reactpy-docs.herokuapp.com/docs/guides/creating-interfaces/your-first-components/index.html#parametrizing-components). These components can utilize [hooks](https://reactpy-docs.herokuapp.com/docs/reference/hooks-api.html) and [events](https://reactpy-docs.herokuapp.com/docs/guides/adding-interactivity/responding-to-events/index.html#async-event-handlers) to create infinitely complex web pages.

When needed, ReactPy can [use components directly from NPM](https://reactpy-docs.herokuapp.com/docs/guides/escape-hatches/javascript-components.html#dynamically-loaded-components). For additional flexibility, components can also be [fully developed in JavaScript](https://reactpy-docs.herokuapp.com/docs/guides/escape-hatches/javascript-components.html#custom-javascript-components).

Any Python web framework with Websockets can support ReactPy. See below for what frameworks are supported out of the box.

| Supported Frameworks                                                                                                                                          | Supported Frameworks (External)                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`Flask`, `FastAPI`, `Sanic`, `Tornado`](https://reactpy-docs.herokuapp.com/docs/guides/getting-started/installing-reactpy.html#officially-supported-servers) | [`Django`](https://github.com/reactive-python/django-reactpy), [`Plotly-Dash`](https://github.com/reactive-python/reactpy-dash), [`Jupyter`](https://github.com/reactive-python/reactpy-jupyter) |

# At a Glance

To get a rough idea of how to write apps in ReactPy, take a look at this tiny _Hello World_ application.

```python
from reactpy import component, html, run

@component
def HelloWorld():
    return html.h1("Hello, World!")

run(HelloWorld)
```

# Resources

Follow the links below to find out more about this project.

- [Try it Now](https://mybinder.org/v2/gh/reactive-python/reactpy-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out ReactPy in a Jupyter Notebook.
- [Documentation](https://reactpy-docs.herokuapp.com/) - learn how to install, run, and use ReactPy.
- [Community Forum](https://github.com/reactive-python/reactpy/discussions) - ask questions, share ideas, and show off projects.
- [Contributor Guide](https://reactpy-docs.herokuapp.com/docs/developing-reactpy/contributor-guide.html) - see how you can help develop this project.
- [Code of Conduct](https://github.com/reactive-python/reactpy/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.
