from reactpy import component, html, use_connection

# start


@component
def connection_report():
    connection = use_connection()

    # Three things, three sources: `scope` is what the ASGI server received,
    # `location` is the URL the browser reported, `carrier` is the object
    # mediating the connection (a websocket for the ASGI executors).
    return html.div(
        html.h1("Who is connected"),
        html.p(f"peer: {connection.scope['client']}"),
        html.p(f"page: {connection.location.path}"),
        html.p(f"protocol: {connection.scope['type']}"),
        html.p(f"carrier: {type(connection.carrier).__name__}"),
    )
