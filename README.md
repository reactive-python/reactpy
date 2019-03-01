# iDOM

Libraries for defining and controlling interactive webpages with Python 3.6 and above.

* [Python Documentation](https://github.com/rmorshea/idom/blob/master/idom/py/README.md)
* [Javascript Documentation](https://github.com/rmorshea/idom/blob/master/idom/js/README.md)


# At a Glance

We can use iDOM to create a simple slide show which changes whenever a use clicks an image.

```python
import idom


@idom.element
async def slideshow(self, index=0):
    image = idom.node("img", src=f"https://picsum.photos/800/300?image={index}")
    image.attributes["style"]["border"] = "2px solid blue"

    events = image.eventHandlers = idom.Events()

    @events.on("click")
    def change():
        self.update(index + 1)

    return image


idom.SimpleWebServer(slideshow).daemon("localhost", 8765).join()
```

Running this will server our slideshow to `"https://localhost:8765/idom/client/index.html"`

<img src='https://picsum.photos/800/300?random' style='border: 2px solid blue'/>

You could even display the same thing in a Jupyter notebook!

```python
idom.display("jupyter", "https://localhost:8765/idom/stream")
```

Every click will then cause the image to change (it won't here of course).
