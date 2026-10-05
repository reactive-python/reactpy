from reactpy import component, html

# start
guest = 0


@component
def cup():
    # Bad: changing a preexisting variable!
    global guest
    guest = guest + 1
    return html.h2(f"Tea cup for guest #{guest}")


@component
def tea_set():
    return html(cup(), cup(), cup())
