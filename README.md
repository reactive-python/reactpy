# IDOM &middot; [![Tests](https://github.com/idom-team/idom/workflows/Test/badge.svg?event=push)](https://github.com/idom-team/idom/actions?query=workflow%3ATest) [![PyPI Version](https://img.shields.io/pypi/v/idom.svg)](https://pypi.python.org/pypi/idom) [![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://github.com/idom-team/idom/blob/main/LICENSE)

IDOM is a Python library for creating user interfaces.

Any application created with IDOM sits atop a foundation of
[“components”](https://idom-docs.herokuapp.com/docs/guides/creating-interfaces/your-first-components/index.html) - reusable chunks of code built from small [elements of functionality](https://idom-docs.herokuapp.com/docs/guides/creating-interfaces/html-with-idom/index.html) like buttons, text,
and images. Within each component you can then [add interactivity](https://idom-docs.herokuapp.com/docs/guides/adding-interactivity/index.html) through declarative state
hooks and event handlers.

IDOM is most commonly used to **create web-based interactive interfaces without
writing any JavaScript!** This is done in conjunction with [supported web
frameworks](https://idom-docs.herokuapp.com/docs/guides/getting-started/installing-idom.html#native-backends)
like FastAPI, Flask, and Tornado, or with [other
platforms](https://idom-docs.herokuapp.com/docs/guides/getting-started/installing-idom.html#other-platforms)
like Jupyter, Django, and Plotly Dash.

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

- [Try it Now](https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out IDOM in a Jupyter Notebook.
- [Documentation](https://idom-docs.herokuapp.com/) - learn how to install, run, and use IDOM.
- [Community Forum](https://github.com/idom-team/idom/discussions) - ask questions, share ideas, and show off projects.
- [Contributor Guide](https://idom-docs.herokuapp.com/docs/developing-idom/contributor-guide.html) - see how you can help develop this project.
- [Code of Conduct](https://github.com/idom-team/idom/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.
