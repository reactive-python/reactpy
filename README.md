# IDOM &middot; [![Tests](https://github.com/idom-team/idom/workflows/Test/badge.svg?event=push)](https://github.com/idom-team/idom/actions?query=workflow%3ATest) [![PyPI Version](https://img.shields.io/pypi/v/idom.svg)](https://pypi.python.org/pypi/idom) [![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://github.com/idom-team/idom/blob/main/LICENSE)

IDOM is a Python web framework for building **interactive websites without needing a
single line of Javascript**. These sites are built from small elements of functionality
like buttons text and images. IDOM allows you to combine these elements into reusable
"components" that can be composed together to create complex views.

Ecosystem independence is also a core feature of IDOM. It can be added to existing
applications built on a variety of sync and async web servers, as well as integrated
with other frameworks like Django, Jupyter, and Plotly Dash. Not only does this mean
you're free to choose what technology stack to run on, but on top of that, you can run
the exact same components wherever you need them. For example, you can take a component
originally developed in a Jupyter Notebook and embed it in your production application
without changing anything about the component itself.

# At a Glance

To get a rough idea of how to write apps in IDOM, take a look at the tiny "hello
world" application below:

```python
from idom import component, html, run

@component
def App():
    return html.h1("Hello, World!")

run(App)
```

# Resources

Follow the links below to find out more about this project

- [Try it Now](https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out IDOM in a Jupyter Notebook.
- [Documentation](https://idom-docs.herokuapp.com/) - learn how to install, run, and use IDOM.
- [Community Forum](https://github.com/idom-team/idom/discussions) - ask questions, share ideas, and show off projects.
- [Contributor Guide](https://idom-docs.herokuapp.com/docs/developing-idom/contributor-guide.html) - see how you can help develop this project.
- [Code of Conduct](https://github.com/idom-team/idom/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.
