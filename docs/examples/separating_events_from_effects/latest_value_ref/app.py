"""When a callback really must stay stable *and* read the newest value, keep
that value in a ref and read `.current` at call time.
"""

from reactpy import component, html, use_callback, use_ref, use_state


# start
@component
def checkout():
    coupon, set_coupon = use_state("")
    total, set_total = use_state(0)
    coupon_ref = use_ref("")
    # updated during render, so any callback reads the value as of the click
    coupon_ref.current = coupon

    # pinned to nothing: the identity never changes, yet it reads `coupon_ref`
    async def apply_coupon_handler(event):
        print(f"applying coupon={coupon_ref.current!r}")

    apply_coupon = use_callback(apply_coupon_handler, dependencies=[])

    async def handle_coupon_change(e):
        # The await comes first: `.upper()` runs on the string which comes back,
        # not on the proxy. Without the parens you would call `.upper()` on the
        # proxy itself and silently get the un-uppercased value.
        set_coupon((await e.target.value).upper())

    async def handle_total_click(e):
        set_total(total + 10)

    return html.div(
        html.input(
            {
                "value": coupon,
                "onChange": handle_coupon_change,
            }
        ),
        html.button({"onClick": apply_coupon}, "Apply coupon"),
        html.button({"onClick": handle_total_click}, f"Total {total}"),
        html.p(f"page shows coupon={coupon!r} — compare with the console"),
    )


@component
def app():
    return checkout()
