from gallery import gallery, profile

from reactpy import component, html


@component
def app():
    return html.div(profile(), gallery())
