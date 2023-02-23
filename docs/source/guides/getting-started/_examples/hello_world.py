from reactpy import component, html, run


@component
def App():
    return html.h1("Hello, world!")


run(App)
