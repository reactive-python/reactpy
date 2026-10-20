from reactpy import component, html


# start
@component
def cup(guest):
    return html.h2(f"Tea cup for guest #{guest}")


@component
def tea_set():
    return html(cup(1), cup(2), cup(3))
