from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from reactpy.core.vdom import custom_vdom_constructor, make_vdom_constructor

if TYPE_CHECKING:
    from reactpy.core.types import (
        EventHandlerDict,
        Key,
        VdomAttributes,
        VdomChild,
        VdomChildren,
        VdomDict,
        VdomDictConstructor,
    )

__all__ = ["html"]

NO_CHILDREN_ALLOWED_HTML_BODY = {
    "area",
    "base",
    "br",
    "col",
    "command",
    "embed",
    "hr",
    "img",
    "input",
    "iframe",
    "keygen",
    "link",
    "meta",
    "param",
    "portal",
    "source",
    "track",
    "wbr",
}

NO_CHILDREN_ALLOWED_SVG = {
    "animate",
    "animateMotion",
    "animateTransform",
    "circle",
    "desc",
    "discard",
    "ellipse",
    "feBlend",
    "feColorMatrix",
    "feComponentTransfer",
    "feComposite",
    "feConvolveMatrix",
    "feDiffuseLighting",
    "feDisplacementMap",
    "feDistantLight",
    "feDropShadow",
    "feFlood",
    "feFuncA",
    "feFuncB",
    "feFuncG",
    "feFuncR",
    "feGaussianBlur",
    "feImage",
    "feMerge",
    "feMergeNode",
    "feMorphology",
    "feOffset",
    "fePointLight",
    "feSpecularLighting",
    "feSpotLight",
    "feTile",
    "feTurbulence",
    "filter",
    "foreignObject",
    "hatch",
    "hatchpath",
    "image",
    "line",
    "linearGradient",
    "metadata",
    "mpath",
    "path",
    "polygon",
    "polyline",
    "radialGradient",
    "rect",
    "script",
    "set",
    "stop",
    "style",
    "text",
    "textPath",
    "title",
    "tspan",
    "use",
    "view",
}


def _fragment(
    attributes: VdomAttributes,
    children: Sequence[VdomChild],
    key: Key | None,
    event_handlers: EventHandlerDict,
) -> VdomDict:
    """An HTML fragment - this element will not appear in the DOM"""
    if attributes or event_handlers:
        msg = "Fragments cannot have attributes besides 'key'"
        raise TypeError(msg)
    model: VdomDict = {"tagName": ""}

    if children:
        model["children"] = children

    if key is not None:
        model["key"] = key

    return model


def _script(
    attributes: VdomAttributes,
    children: Sequence[VdomChild],
    key: Key | None,
    event_handlers: EventHandlerDict,
) -> VdomDict:
    """Create a new `<script> <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script>`__ element.

    .. warning::

        Be careful to sanitize data from untrusted sources before using it in a script.
        See the "Notes" for more details

    This behaves slightly differently than a normal script element in that it may be run
    multiple times if its key changes (depending on specific browser behaviors). If no
    key is given, the key is inferred to be the content of the script or, lastly its
    'src' attribute if that is given.

    Notes:
        Do not use unsanitized data from untrusted sources anywhere in your script.
        Doing so may allow for malicious code injection
        (`XSS <https://en.wikipedia.org/wiki/Cross-site_scripting>`__`).
    """
    model: VdomDict = {"tagName": "script"}

    if event_handlers:
        msg = "'script' elements do not support event handlers"
        raise ValueError(msg)

    if children:
        if len(children) > 1:
            msg = "'script' nodes may have, at most, one child."
            raise ValueError(msg)
        if not isinstance(children[0], str):
            msg = "The child of a 'script' must be a string."
            raise ValueError(msg)
        model["children"] = children
        if key is None:
            key = children[0]

    if attributes:
        model["attributes"] = attributes
        if key is None and not children and "src" in attributes:
            key = attributes["src"]

    if key is not None:
        model["key"] = key

    return model


class SvgConstructor:
    """Constructor specifically for SVG children."""

    __cache__: ClassVar[dict[str, VdomDictConstructor]] = {}

    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict:
        return self.svg(*attributes_and_children)

    def __getattr__(self, value: str) -> VdomDictConstructor:
        value = value.rstrip("_").replace("_", "-")

        if value in self.__cache__:
            return self.__cache__[value]

        self.__cache__[value] = make_vdom_constructor(
            value, allow_children=value not in NO_CHILDREN_ALLOWED_SVG
        )

        return self.__cache__[value]

    # SVG child elements, written out here for auto-complete purposes
    # The actual elements are created dynamically in the __getattr__ method.
    # Elements other than these can still be created.
    a: VdomDictConstructor
    animate: VdomDictConstructor
    animateMotion: VdomDictConstructor
    animateTransform: VdomDictConstructor
    circle: VdomDictConstructor
    clipPath: VdomDictConstructor
    defs: VdomDictConstructor
    desc: VdomDictConstructor
    discard: VdomDictConstructor
    ellipse: VdomDictConstructor
    feBlend: VdomDictConstructor
    feColorMatrix: VdomDictConstructor
    feComponentTransfer: VdomDictConstructor
    feComposite: VdomDictConstructor
    feConvolveMatrix: VdomDictConstructor
    feDiffuseLighting: VdomDictConstructor
    feDisplacementMap: VdomDictConstructor
    feDistantLight: VdomDictConstructor
    feDropShadow: VdomDictConstructor
    feFlood: VdomDictConstructor
    feFuncA: VdomDictConstructor
    feFuncB: VdomDictConstructor
    feFuncG: VdomDictConstructor
    feFuncR: VdomDictConstructor
    feGaussianBlur: VdomDictConstructor
    feImage: VdomDictConstructor
    feMerge: VdomDictConstructor
    feMergeNode: VdomDictConstructor
    feMorphology: VdomDictConstructor
    feOffset: VdomDictConstructor
    fePointLight: VdomDictConstructor
    feSpecularLighting: VdomDictConstructor
    feSpotLight: VdomDictConstructor
    feTile: VdomDictConstructor
    feTurbulence: VdomDictConstructor
    filter: VdomDictConstructor
    foreignObject: VdomDictConstructor
    g: VdomDictConstructor
    hatch: VdomDictConstructor
    hatchpath: VdomDictConstructor
    image: VdomDictConstructor
    line: VdomDictConstructor
    linearGradient: VdomDictConstructor
    marker: VdomDictConstructor
    mask: VdomDictConstructor
    metadata: VdomDictConstructor
    mpath: VdomDictConstructor
    path: VdomDictConstructor
    pattern: VdomDictConstructor
    polygon: VdomDictConstructor
    polyline: VdomDictConstructor
    radialGradient: VdomDictConstructor
    rect: VdomDictConstructor
    script: VdomDictConstructor
    set: VdomDictConstructor
    stop: VdomDictConstructor
    style: VdomDictConstructor
    switch: VdomDictConstructor
    symbol: VdomDictConstructor
    text: VdomDictConstructor
    textPath: VdomDictConstructor
    title: VdomDictConstructor
    tspan: VdomDictConstructor
    use: VdomDictConstructor
    view: VdomDictConstructor


class HtmlConstructor:
    """Create a new HTML element. Commonly used elements are provided via auto-complete.
    However, any HTML element can be created by calling the element name as an attribute.

    If trying to create an element that is illegal syntax in Python, you can postfix an
    underscore character (eg. `html.del_` for `<del>`).

    If trying to create an element with dashes in the name, you can replace the dashes
    with underscores (eg. `html.data_table` for `<data-table>`)."""

    # ruff: noqa: N815
    __cache__: ClassVar[dict[str, VdomDictConstructor]] = {
        "script": custom_vdom_constructor(_script),
        "fragment": custom_vdom_constructor(_fragment),
    }

    def __getattr__(self, value: str) -> VdomDictConstructor:
        value = value.rstrip("_").replace("_", "-")

        if value in self.__cache__:
            return self.__cache__[value]

        self.__cache__[value] = make_vdom_constructor(
            value, allow_children=value not in NO_CHILDREN_ALLOWED_HTML_BODY
        )

        return self.__cache__[value]

    # HTML elements, written out here for auto-complete purposes
    # The actual elements are created dynamically in the __getattr__ method.
    # Elements other than these can still be created.
    a: VdomDictConstructor
    abbr: VdomDictConstructor
    address: VdomDictConstructor
    area: VdomDictConstructor
    article: VdomDictConstructor
    aside: VdomDictConstructor
    audio: VdomDictConstructor
    b: VdomDictConstructor
    body: VdomDictConstructor
    base: VdomDictConstructor
    bdi: VdomDictConstructor
    bdo: VdomDictConstructor
    blockquote: VdomDictConstructor
    br: VdomDictConstructor
    button: VdomDictConstructor
    canvas: VdomDictConstructor
    caption: VdomDictConstructor
    cite: VdomDictConstructor
    code: VdomDictConstructor
    col: VdomDictConstructor
    colgroup: VdomDictConstructor
    data: VdomDictConstructor
    dd: VdomDictConstructor
    del_: VdomDictConstructor
    details: VdomDictConstructor
    dialog: VdomDictConstructor
    div: VdomDictConstructor
    dl: VdomDictConstructor
    dt: VdomDictConstructor
    em: VdomDictConstructor
    embed: VdomDictConstructor
    fieldset: VdomDictConstructor
    figcaption: VdomDictConstructor
    figure: VdomDictConstructor
    footer: VdomDictConstructor
    form: VdomDictConstructor
    h1: VdomDictConstructor
    h2: VdomDictConstructor
    h3: VdomDictConstructor
    h4: VdomDictConstructor
    h5: VdomDictConstructor
    h6: VdomDictConstructor
    head: VdomDictConstructor
    header: VdomDictConstructor
    hr: VdomDictConstructor
    html: VdomDictConstructor
    i: VdomDictConstructor
    iframe: VdomDictConstructor
    img: VdomDictConstructor
    input: VdomDictConstructor
    ins: VdomDictConstructor
    kbd: VdomDictConstructor
    label: VdomDictConstructor
    legend: VdomDictConstructor
    li: VdomDictConstructor
    link: VdomDictConstructor
    main: VdomDictConstructor
    map: VdomDictConstructor
    mark: VdomDictConstructor
    math: VdomDictConstructor
    menu: VdomDictConstructor
    menuitem: VdomDictConstructor
    meta: VdomDictConstructor
    meter: VdomDictConstructor
    nav: VdomDictConstructor
    noscript: VdomDictConstructor
    object: VdomDictConstructor
    ol: VdomDictConstructor
    option: VdomDictConstructor
    output: VdomDictConstructor
    p: VdomDictConstructor
    param: VdomDictConstructor
    picture: VdomDictConstructor
    portal: VdomDictConstructor
    pre: VdomDictConstructor
    progress: VdomDictConstructor
    q: VdomDictConstructor
    rp: VdomDictConstructor
    rt: VdomDictConstructor
    ruby: VdomDictConstructor
    s: VdomDictConstructor
    samp: VdomDictConstructor
    script: VdomDictConstructor
    section: VdomDictConstructor
    select: VdomDictConstructor
    slot: VdomDictConstructor
    small: VdomDictConstructor
    source: VdomDictConstructor
    span: VdomDictConstructor
    strong: VdomDictConstructor
    style: VdomDictConstructor
    sub: VdomDictConstructor
    summary: VdomDictConstructor
    sup: VdomDictConstructor
    table: VdomDictConstructor
    tbody: VdomDictConstructor
    td: VdomDictConstructor
    template: VdomDictConstructor
    textarea: VdomDictConstructor
    tfoot: VdomDictConstructor
    th: VdomDictConstructor
    thead: VdomDictConstructor
    time: VdomDictConstructor
    title: VdomDictConstructor
    tr: VdomDictConstructor
    track: VdomDictConstructor
    u: VdomDictConstructor
    ul: VdomDictConstructor
    var: VdomDictConstructor
    video: VdomDictConstructor
    wbr: VdomDictConstructor
    fragment: VdomDictConstructor

    # Special Case: SVG elements
    # Since SVG elements have a different set of allowed children, they are
    # separated into a different constructor, and are accessed via `html.svg.example()`
    svg: SvgConstructor = SvgConstructor()


html = HtmlConstructor()
