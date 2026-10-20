from reactpy import component, create_context, html, use_context, use_effect

# start

Config = create_context({"endpoint": "https://api.example"})


@component
def status():
    # Read the context HERE, during the render. An effect body runs later, in
    # its own task, where no hook is active -- calling use_context there fails
    # with `RuntimeError: No life cycle hook is active.` Capture the value in a
    # local and let the closure carry it into the effect.
    config = use_context(Config)

    def on_mount():
        print(f"polling {config['endpoint']}")

    use_effect(on_mount, dependencies=[config])
    return html.p(f"endpoint: {config['endpoint']}")
