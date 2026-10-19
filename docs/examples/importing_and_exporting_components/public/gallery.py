from reactpy import component, html

__all__ = ["gallery", "profile"]


@component
def profile():
    return html.img(
        {"src": "../../assets/images/demos/QIrZWGIs.jpg", "alt": "Alan L. Hart"}
    )


@component
def gallery():
    return html.section(
        html.h1("Amazing scientists"),
        profile(),
        profile(),
        profile(),
    )
