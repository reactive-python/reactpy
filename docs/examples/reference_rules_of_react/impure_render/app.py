from reactpy import component, html, use_state

# start

# Module-level state is shared by every connection and survives across renders,
# so `total` is not part of the component's inputs at all. Two browsers, or two
# renders of the same component, see the same counter.
total = 0


@component
def impure_counter():
    global total
    count, set_count = use_state(0)

    # Render mutates module state: an outside effect, and a value that changes
    # what the next render returns even though nothing the component received
    # changed. Nothing warns about this -- the symptom is a number that does not
    # match the button presses.
    total += 1

    return html.div(
        html.h1(count),
        html.p(f"renders (module-wide): {total}"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )
