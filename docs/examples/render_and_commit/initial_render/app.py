from reactpy import component, html
from reactpy.executors.asgi import ReactPy


# start
@component
def image():
    return html.img(
        {
            "src": "https://i.imgur.com/ZF6s192.jpg",
            "alt": "'Floralis Genérica' by Eduardo Catalano: a gigantic "
            "metallic flower sculpture with reflective petals",
        }
    )


# Mounting is what triggers the initial render. Which line you use depends on
# how the app is served; see the executors reference.
my_app = ReactPy(image)
