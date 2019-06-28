# iDOM

<a href="https://travis-ci.com/rmorshea/idom">
  <img alt="Build Status" src="https://travis-ci.com/rmorshea/idom.svg?branch=master"/>
</a>
<a href="https://pypi.python.org/pypi/idom">
  <img alt="Version Info" src="https://img.shields.io/pypi/v/idom.svg"/>
</a>
<a href="https://github.com/rmorshea/idom/blob/master/LICENSE"/>
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-purple.svg">
</a>

Libraries for creating and controlling interactive web pages with Python 3.6 and above.

* [Python Documentation](https://idom.readthedocs.io/en/latest/)
* [Javascript Documentation](https://github.com/rmorshea/idom/blob/master/src/js/README.md)

iDOM is still young. If you have ideas or find a bug, be sure to post an
[issue](https://github.com/rmorshea/idom/issues)
or create a
[pull request](https://github.com/rmorshea/idom/pulls). Thanks in advance!


<h3>
  <a href="https://mybinder.org/v2/gh/rmorshea/idom/master?filepath=examples%2Fintroduction.ipynb">
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
pip install idom
```


# At a Glance

iDOM can be used to create a simple slideshow which changes whenever a user clicks an image.

```python
import idom

@idom.element
async def Slideshow(self, index=0):

    async def next_image(event):
        self.update(index + 1)

    url = f"https://picsum.photos/800/300?image={index}"
    return idom.node("img", src=url, onClick=next_image)

server = idom.server.sanic.PerClientState(Slideshow)
server.daemon("localhost", 8765).join()
```

Running this will serve our slideshow to `"https://localhost:8765/client/index.html"`

<img src='https://picsum.photos/800/300?random'/>

You could even display the same thing in a Jupyter notebook!

```python
idom.display("jupyter", "https://localhost:8765/stream")
```

Every click will then cause the image to change (it won't here of course).
