# iDOM

Libraries for defining and controlling interactive webpages with Python 3.6 and above.

* [Python Documentation](https://github.com/rmorshea/idom/blob/master/idom/py/README.md)
* [Javascript Documentation](https://github.com/rmorshea/idom/blob/master/idom/js/README.md)

# Early Days

iDOM is still young. If you have ideas or find a bug, be sure to post an
[issue](https://github.com/rmorshea/idom/issues)
or create a
[pull request](https://github.com/rmorshea/idom/pulls).
We need all the help we can get!


# At a Glance

iDOM can be used to create a simple slideshow which changes whenever a user clicks an image.

```python
import idom

@idom.element
async def slideshow(self, index=0):
    image = idom.node("img", src=f"https://picsum.photos/800/300?image={index}")
    image.eventHandlers = idom.Events()

    @image.eventHandlers.on("click")
    def change():
        self.update(index + 1)

    return image

idom.SimpleWebServer(slideshow).daemon("localhost", 8765).join()
```

Running this will server our slideshow to `"https://localhost:8765/idom/client/index.html"`

<img src='https://picsum.photos/800/300?random'/>

You could even display the same thing in a Jupyter notebook!

```python
idom.display("jupyter", "https://localhost:8765/idom/stream")
```

Every click will then cause the image to change (it won't here of course).


# Breaking it Down

That might have been a bit much to throw out at once. Let's break down each piece of the
example above:

```python
...

@idom.element
async def slideshow(self, index=0):

...
```

The decorator indicates that the function or coroutine to follow defines a "stateful"
element. The `slideshow` coroutine is responsible for building a DOM model. Every time
we update the slideshow it will be called again to update that DOM model with any
necessary changes.

As we mentioned, this is a "stateful" element which means that the first parameter of
the function is an `Element` object. The other parameters with default values define
what state the element has. In this case `index` would be part of the element's state
because it has a default value of `0`.

```python
    image = idom.node("img", src=f"https://picsum.photos/800/300?image={index}")
    image.eventHandlers = idom.Events()
```

We assign a DOM model to `image` which will display an image from
https://picsum.photos.
Elements can be manually defined using dictionaries that adhere to the
[VDOM mimetype specification](https://github.com/nteract/vdom/blob/master/docs/mimetype-spec.md),
or via the `idom.node` helper function. Instead of returning a dictionary `idom.node`
returns a dictionary with attribute access.

Assigning a new `idom.Events()` object
to the image's `eventHandlers` adds the ability to respond to events that may be
triggered when users interact with the image. Similarly to the mimetype specification,
events can also be manually defined using a dictionary which adheres to the
[VDOM event specification](https://github.com/nteract/vdom/blob/master/docs/event-spec.md),
but can be done easier via the `idom.Event` object.

```python
    @image.EventHandlers.on("click")
    def change():
        self.update(index + 1)
```

By using the `idom.Events()` object that was just assigned to the image, we can
register a function as an event handler. This handler will be called once a user
clicks on the image. All supported events are listed
[here](https://reactjs.org/docs/events.html).

You can add parameters to this handler which will allow you to access attributes of the
JavaScript event which occurred in the browser. For example when a key is pressed in
an `<input/>` element you can access the key's name by adding a `key` parameter to
the event handler.

Calling `self.update(*args, **kwargs)` where `self` is an `Element` will schedule a
new render of the `slideshow` element to be performed. This will call the coroutine
with any new parameters but also pass "stateful" parameters as well.

```python
    return image
```

Finally returns the DOM model that will be displayed.

```python
idom.SimpleWebServer(slideshow).daemon("localhost", 8765).join()
```

This sets up a simple web server which will display the layout of elements and update
them when events occur over a websocket. To display the layout we can navigate to
http://localhost:8765/idom/client/index.html or use `idom.display()` to show it
in a Jupyter Notebook via a widget. The exact protocol for communicating DOM models
over a network is not documented yet.
