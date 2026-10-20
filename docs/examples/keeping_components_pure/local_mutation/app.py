from reactpy import component, html


# start
@component
def cup(guest):
    return html.h2(f"Tea cup for guest #{guest}")


@component
def tea_gathering():
    cups = []
    for index in range(1, 13):
        cups.append(cup(index, key=index))
    return html.div(cups)
