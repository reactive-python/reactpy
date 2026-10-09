"""Read the newest value from a long-lived Effect using a ref."""

import asyncio

from reactpy import component, html, use_async_effect, use_ref, use_state

SLOW_LATENCY = 30
HIGH_THRESHOLD = 50
LOW_THRESHOLD = 10


def append_alert(previous):
    """A module-level updater, so the Effect's loop builds no closures."""
    return [*previous, f"slow: {SLOW_LATENCY}ms"]


# start
@component
def connection_monitor():
    threshold, set_threshold = use_state(HIGH_THRESHOLD)
    alerts, set_alerts = use_state([])
    # Write the newest value during render so a reader that wakes up later
    # gets this render's number rather than the one captured at mount.
    latest_threshold = use_ref(threshold)
    latest_threshold.current = threshold

    async def watch():
        while True:
            await asyncio.sleep(0.2)
            # SLOW_LATENCY stands in for a real measurement.
            if SLOW_LATENCY > latest_threshold.current:
                set_alerts(append_alert)

    # `dependencies=[]` keeps ONE task alive for the component's lifetime.
    # Reading `threshold` directly here would freeze it at its first value.
    use_async_effect(watch, dependencies=[])

    return html.div(
        html.p(f"threshold: {threshold}"),
        html.button(
            {
                "onClick": lambda event: set_threshold(
                    LOW_THRESHOLD if threshold == HIGH_THRESHOLD else HIGH_THRESHOLD
                )
            },
            "Toggle threshold",
        ),
        html.p(f"alerts: {len(alerts)}"),
    )


# end
