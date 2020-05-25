from functools import wraps

import idom


def click_to_start(element):
    """Simple tool used to block animating widgets from displaying until clicked"""

    @wraps(element)
    @idom.element
    async def wrapper(self, *args, **kwargs):
        async def start_on_click(event):
            alt.update(show=True)

        alt = UseAlternateUntilShown(
            idom.html.button({"onClick": start_on_click}, "Click To Start"),
            element(*args, **kwargs),
        )

        return alt

    return wrapper


@idom.element(state="element, alternate")
async def UseAlternateUntilShown(self, alternate, element, show=False):
    if show:
        return element
    else:
        return alternate
