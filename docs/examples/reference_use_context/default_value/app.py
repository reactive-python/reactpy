# start
from reactpy import component, create_context, html, use_context
from reactpy.types import Context

# The annotation is what lets the value be a list *or* the None default. Without
# it, create_context(None) fixes the value type to None and a type checker then
# rejects `value=[...]`.
Cart: Context[list[str] | None] = create_context(None)


@component
def cart_badge():
    # With no provider above, use_context returns the default given to
    # create_context. Choosing that default well is what lets a component
    # render -- or be tested -- on its own, with no provider wrapper.
    items = use_context(Cart)
    if items is None:
        return html.p("cart: not available")
    return html.p(f"cart: {len(items)} item(s)")


@component
def shop():
    return html.div(cart_badge())


@component
def shop_with_cart():
    return Cart(shop(), value=["widget", "gadget", "gizmo"])
