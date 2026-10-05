from reactpy import component, html, use_memo, use_state

# start


@component
def totals():
    items, set_items = use_state([1, 2, 3])
    tax_rate, set_tax_rate = use_state(0.0)

    # `tax_rate` is read here but deliberately left out of `dependencies`.
    # ReactPy does not complain. The cached total just keeps the rate from the
    # render that last computed it, so "Add 10% tax" appears to do nothing --
    # until something that *is* a dependency changes, and the stale number
    # jumps to the right one all at once.
    def grand_total():
        return sum(items) * (1 + tax_rate)

    total = use_memo(grand_total, dependencies=[items])

    return html.div(
        html.h1(f"total: {total:.2f}"),
        html.p(f"tax rate: {tax_rate:.0%}"),
        html.button(
            {"onClick": lambda event: set_tax_rate(tax_rate + 0.1)}, "Add 10% tax"
        ),
        html.button(
            {"onClick": lambda event: set_items([*items, len(items) + 1])},
            "Add an item",
        ),
    )
