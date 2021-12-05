import idom


pigeon_maps = idom.web.module_from_template("react", "pigeon-maps", fallback="⌛")
Map, Marker = idom.web.export(pigeon_maps, ["Map", "Marker"])


@idom.component
def MapWithMarkers():
    marker_anchor, add_marker_anchor, remove_marker_anchor = use_set()

    markers = list(
        map(
            lambda anchor: Marker(
                {
                    "anchor": anchor,
                    "onClick": lambda: remove_marker_anchor(anchor),
                },
                key=str(anchor),
            ),
            marker_anchor,
        )
    )

    return Map(
        {
            "defaultCenter": (37.774, -122.419),
            "defaultZoom": 12,
            "height": "300px",
            "metaWheelZoom": True,
            "onClick": lambda event: add_marker_anchor(tuple(event["latLng"])),
        },
        markers,
    )


def use_set(initial_value=None):
    values, set_values = idom.hooks.use_state(initial_value or set())

    def add_value(lat_lon):
        set_values(values.union({lat_lon}))

    def remove_value(lat_lon):
        set_values(values.difference({lat_lon}))

    return values, add_value, remove_value


idom.run(MapWithMarkers)
