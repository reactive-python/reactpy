from reactpy import component, html, use_scope

# start


def header(scope, name):
    """Read one request header out of an ASGI scope.

    Headers arrive as a list of ``(bytes, bytes)`` pairs, lower-cased by the
    server, so both halves need decoding before you can compare them.
    """
    wanted = name.lower().encode()
    for key, value in scope.get("headers", []):
        if key == wanted:
            return value.decode()
    return None


@component
def visitor():
    scope = use_scope()
    # Note this is the *websocket* scope. Its "path" is the ReactPy websocket
    # path, not the page the visitor is on -- use use_location() for that.
    # `client` is legitimately absent or None behind some proxies, so read it
    # through a local and check it rather than subscripting the scope directly.
    client = scope.get("client")
    peer = client[0] if client else "unknown"
    return html.div(
        html.h1(f"Hello, {peer}"),
        html.p(f"browser: {header(scope, 'user-agent') or 'unknown'}"),
        html.p(f"connection type: {scope['type']}"),
    )
