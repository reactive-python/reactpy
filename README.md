# IDOM

<a href="https://github.com/idom-team/idom/actions?query=workflow%3ATest">
  <img alt="Tests" src="https://github.com/idom-team/idom/workflows/Test/badge.svg?event=push" />
</a>
<a href="https://codecov.io/gh/rmorshea/idom">
  <img alt="Code Coverage" src="https://codecov.io/gh/rmorshea/idom/branch/main/graph/badge.svg" />
</a>
<a href="https://pypi.python.org/pypi/idom">
  <img alt="Version Info" src="https://img.shields.io/pypi/v/idom.svg"/>
</a>
<a href="https://github.com/rmorshea/idom/blob/main/LICENSE">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-purple.svg">
</a>

Libraries for creating and controlling interactive web pages with Python 3.7 and above.

**Be sure to [read the Documentation](https://idom-docs.herokuapp.com)**

IDOM is still young. If you have ideas or find a bug, be sure to post an
[issue](https://github.com/rmorshea/idom/issues)
or create a
[pull request](https://github.com/rmorshea/idom/pulls). Thanks in advance!

<h3>
  <a
    target="_blank"
    href="https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?filepath=notebooks%2Fintroduction.ipynb"
  >
    Try it Now
    <img alt="Binder" valign="bottom" height="25px"
    src="https://mybinder.org/badge_logo.svg"
    />
  </a>
</h3>

Click the badge above to get started! It will take you to a [Jupyter Notebooks](https://jupyter.org/)
hosted by [Binder](https://mybinder.org/) with some great examples.

### Or Install it Now

```bash
pip install idom[stable]
```

# At a Glance

IDOM can be used to create a simple slideshow which changes whenever a user clicks an image.

```python
import idom

@idom.component
def Slideshow():
    index, set_index = idom.hooks.use_state(0)
    url = f"https://picsum.photos/800/300?image={index}"
    return idom.html.img({"src": url, "onClick": lambda event: set_index(index + 1)})

idom.run(Slideshow, port=8765)
```

Running this will serve our slideshow to `"https://localhost:8765/client/index.html"`

<img src='https://picsum.photos/800/300?random'/>

You can even display the same thing in a Jupyter Notebook, just use [`idom_jupyter`](https://github.com/idom-team/idom-jupyter):
