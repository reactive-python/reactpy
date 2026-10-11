import reactpy

pigeon_maps = reactpy.web.module_from_template("react", "pigeon-maps", fallback="⌛")
Map, Marker = reactpy.web.export(pigeon_maps, ["Map", "Marker"])


@reactpy.component
def MapWithMarkers():
    marker_anchor, add_marker_anchor, remove_marker_anchor = use_set()

    def make_remove_marker_handler(anchor):
        async def remove_marker(event):
            remove_marker_anchor(anchor)

        return remove_marker

    markers = [
        Marker(
            {
                "anchor": anchor,
                "onClick": make_remove_marker_handler(anchor),
            },
            key=str(anchor),
        )
        for anchor in marker_anchor
    ]

    async def add_marker_on_click(event):
        add_marker_anchor(tuple(event["latLng"]))

    return Map(
        {
            "defaultCenter": (37.774, -122.419),
            "defaultZoom": 12,
            "height": "300px",
            "metaWheelZoom": True,
            "onClick": add_marker_on_click,
        },
        markers,
    )


def use_set(initial_value=None):
    values, set_values = reactpy.hooks.use_state(initial_value or set())

    def add_value(lat_lon):
        set_values(values.union({lat_lon}))

    def remove_value(lat_lon):
        set_values(values.difference({lat_lon}))

    return values, add_value, remove_value


reactpy.run(MapWithMarkers)
