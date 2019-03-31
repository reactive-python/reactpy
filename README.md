# iDOM

<a href="https://travis-ci.com/rmorshea/idom">
  <img alt="Build Status" src="https://travis-ci.com/rmorshea/idom.svg?branch=master">
</a>
<a href="https://github.com/rmorshea/idom/blob/master/LICENSE">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-purple.svg">
</a>

Libraries for defining and controlling interactive webpages with Python 3.6 and above.

* [Python Documentation](https://idom.readthedocs.io/en/latest/)
* [Javascript Documentation](https://github.com/rmorshea/idom/blob/master/src/js/README.md)


## Early Days

iDOM is still young. If you have ideas or find a bug, be sure to post an
[issue](https://github.com/rmorshea/idom/issues)
or create a
[pull request](https://github.com/rmorshea/idom/pulls). Thanks in advance!


## At a Glance

iDOM can be used to create a simple slideshow which changes whenever a user clicks an image.

```python
import idom

@idom.element
async def Slideshow(self, index=0):
    events = idom.Events()

    @events.on("click")
    def change():
        self.update(index + 1)

    url = f"https://picsum.photos/800/300?image={index}"
    return idom.node("img", src=url, eventHandlers=events)

idom.StatelessServer(Slideshow).daemon("localhost", 8765).join()
```

Running this will serve our slideshow to `"https://localhost:8765/idom/client/index.html"`

<img src='https://picsum.photos/800/300?random'/>

You could even display the same thing in a Jupyter notebook!

```python
idom.display("jupyter", "https://localhost:8765/idom/stream")
```

Every click will then cause the image to change (it won't here of course).


## Breaking it Down

That might have been a bit much to throw out at once. Let's break down each piece of the
example above:

```python
@idom.element
async def Slideshow(self, index=0):
```

The decorator indicates that the function or coroutine to follow defines an update-able
element. The `Slideshow` coroutine is responsible for building a DOM model, and every
time an update is triggered, it will be called with new parameters to recreate the model.

```python
    events = idom.Events()
```

Creates an object to which event handlers will be assigned. Adding `events` to a DOM
model will given you the ability to respond to events that may be triggered when users
interact with the image. Under the hood though, `events` is just a mapping which
conforms to the
[VDOM event specification](https://github.com/nteract/vdom/blob/master/docs/event-spec.md).

```python
    @events.on("click")
    def change():
        self.update(index + 1)
```

By using the `idom.Events()` object we created above, we can register a function as an
event handler. This handler will be called once a user clicks on the image. All supported
events are listed [here](https://reactjs.org/docs/events.html).

You can add parameters to this handler which will allow you to access attributes of the
JavaScript event which occurred in the browser. For example when a key is pressed in
an `<input/>` element you can access the key's name by adding a `key` parameter to
the event handler.

Inside the handler itself we update `self` which is out `Slideshow` element. Calling
`self.update(*args, **kwargs)` will schedule a new render of the `Slideshow` element to
be performed with new `*args` and `**kwargs`.

```python
    url = f"https://picsum.photos/800/300?image={index}"
    return idom.node("img", src=url, eventHandlers=events)
```

We return a model for an `<img/>` element which draws its image from https://picsum.photos
and will respond to the `events` we defined earlier. Similarly to the `events` object
`idom.node` returns a mapping which conforms to the
[VDOM mimetype specification](https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md)


```python
idom.StatelessServer(Slideshow).daemon("localhost", 8765).join()
```

This sets up a simple web server which will display the layout of elements and update
them when events occur over a websocket. The server is considered "stateless" because
each client that connects to it will see a fresh view. To display the layout we can
navigate to http://localhost:8765/idom/client/index.html or use `idom.display()` to show
it in a Jupyter Notebook via a widget. The exact protocol for communicating DOM models
over a network is not documented yet.
