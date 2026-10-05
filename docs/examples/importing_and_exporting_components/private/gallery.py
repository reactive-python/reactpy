from reactpy import component, html

__all__ = ["gallery"]


@component
def _profile():
    """Used only inside this module, so it stays out of ``__all__``."""
    return html.img({"src": "https://i.imgur.com/QIrZWGIs.jpg", "alt": "Alan L. Hart"})


@component
def gallery():
    return html.section(
        html.h1("Amazing scientists"),
        _profile(),
        _profile(),
        _profile(),
    )
