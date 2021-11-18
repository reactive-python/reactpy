from idom import component, html, run


@component
def App():
    return html.h1("Hello, World!")


run(App)
