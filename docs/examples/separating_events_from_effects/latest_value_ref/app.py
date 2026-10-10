"""When a callback really must stay stable *and* read the newest value, keep
that value in a ref and read `.current` at call time.

# start
"""

from reactpy import component, html, use_callback, use_ref, use_state


@component
def checkout():
    coupon, set_coupon = use_state("")
    total, set_total = use_state(0)
    coupon_ref = use_ref("")
    # updated during render, so any callback reads the value as of the click
    coupon_ref.current = coupon

    # pinned to nothing: the identity never changes, yet it reads `coupon_ref`
    apply_coupon = use_callback(
        lambda event: print(f"applying coupon={coupon_ref.current!r}"),
        dependencies=[],
    )

    return html.div(
        html.input(
            {
                "value": coupon,
                "onChange": lambda e: set_coupon(e["target"]["value"].upper()),
            }
        ),
        html.button({"onClick": apply_coupon}, "Apply coupon"),
        html.button({"onClick": lambda e: set_total(total + 10)}, f"Total {total}"),
        html.p(f"page shows coupon={coupon!r} — compare with the console"),
    )


# end


@component
def app():
    return checkout()
