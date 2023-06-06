from reactpy import component, html, run


@component
def App():
    return html.div(GoodComponent(), BadComponent())


@component
def GoodComponent():
    return html.p("This component rendered successfully")


@component
def BadComponent():
    msg = "This component raised an error"
    raise RuntimeError(msg)


run(App)
