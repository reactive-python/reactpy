from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, overload

from reactpy.core.vdom import Vdom
from reactpy.types import (
    EventHandlerDict,
    Key,
    VdomAttributes,
    VdomChild,
    VdomChildren,
    VdomConstructor,
    VdomDict,
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
    model = VdomDict(tagName="")

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
    model = VdomDict(tagName="script")

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

    __cache__: ClassVar[dict[str, VdomConstructor]] = {}

    @overload
    def __call__(
        self, attributes: VdomAttributes, /, *children: VdomChildren
    ) -> VdomDict: ...

    @overload
    def __call__(self, *children: VdomChildren) -> VdomDict: ...

    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict:
        return self.svg(*attributes_and_children)

    def __getattr__(self, value: str) -> VdomConstructor:
        value = value.rstrip("_").replace("_", "-")

        if value in self.__cache__:
            return self.__cache__[value]

        self.__cache__[value] = Vdom(
            tagName=value, allow_children=value not in NO_CHILDREN_ALLOWED_SVG
        )

        return self.__cache__[value]

    # SVG child elements, written out here for auto-complete purposes
    # The actual elements are created dynamically in the __getattr__ method.
    # Elements other than these can still be created.
    a: VdomConstructor
    animate: VdomConstructor
    animateMotion: VdomConstructor
    animateTransform: VdomConstructor
    circle: VdomConstructor
    clipPath: VdomConstructor
    defs: VdomConstructor
    desc: VdomConstructor
    discard: VdomConstructor
    ellipse: VdomConstructor
    feBlend: VdomConstructor
    feColorMatrix: VdomConstructor
    feComponentTransfer: VdomConstructor
    feComposite: VdomConstructor
    feConvolveMatrix: VdomConstructor
    feDiffuseLighting: VdomConstructor
    feDisplacementMap: VdomConstructor
    feDistantLight: VdomConstructor
    feDropShadow: VdomConstructor
    feFlood: VdomConstructor
    feFuncA: VdomConstructor
    feFuncB: VdomConstructor
    feFuncG: VdomConstructor
    feFuncR: VdomConstructor
    feGaussianBlur: VdomConstructor
    feImage: VdomConstructor
    feMerge: VdomConstructor
    feMergeNode: VdomConstructor
    feMorphology: VdomConstructor
    feOffset: VdomConstructor
    fePointLight: VdomConstructor
    feSpecularLighting: VdomConstructor
    feSpotLight: VdomConstructor
    feTile: VdomConstructor
    feTurbulence: VdomConstructor
    filter: VdomConstructor
    foreignObject: VdomConstructor
    g: VdomConstructor
    hatch: VdomConstructor
    hatchpath: VdomConstructor
    image: VdomConstructor
    line: VdomConstructor
    linearGradient: VdomConstructor
    marker: VdomConstructor
    mask: VdomConstructor
    metadata: VdomConstructor
    mpath: VdomConstructor
    path: VdomConstructor
    pattern: VdomConstructor
    polygon: VdomConstructor
    polyline: VdomConstructor
    radialGradient: VdomConstructor
    rect: VdomConstructor
    script: VdomConstructor
    set: VdomConstructor
    stop: VdomConstructor
    style: VdomConstructor
    switch: VdomConstructor
    symbol: VdomConstructor
    text: VdomConstructor
    textPath: VdomConstructor
    title: VdomConstructor
    tspan: VdomConstructor
    use: VdomConstructor
    view: VdomConstructor
    svg: VdomConstructor


class HtmlConstructor:
    """Create a new HTML element. Commonly used elements are provided via auto-complete.
    However, any HTML element can be created by calling the element name as an attribute.

    If trying to create an element that is illegal syntax in Python, you can postfix an
    underscore character (eg. `html.del_` for `<del>`).

    If trying to create an element with dashes in the name, you can replace the dashes
    with underscores (eg. `html.data_table` for `<data-table>`)."""

    # ruff: noqa: N815
    __cache__: ClassVar[dict[str, VdomConstructor]] = {
        "script": Vdom(tagName="script", custom_constructor=_script),
        "fragment": Vdom(tagName="", custom_constructor=_fragment),
        "svg": SvgConstructor(),
    }

    def __getattr__(self, value: str) -> VdomConstructor:
        value = value.rstrip("_").replace("_", "-")

        if value in self.__cache__:
            return self.__cache__[value]

        self.__cache__[value] = Vdom(
            tagName=value, allow_children=value not in NO_CHILDREN_ALLOWED_HTML_BODY
        )

        return self.__cache__[value]

    # Standard HTML elements are written below for auto-complete purposes
    # The actual elements are created dynamically when __getattr__ is called.
    # Elements other than those type-hinted below can still be created.
    a: VdomConstructor
    abbr: VdomConstructor
    address: VdomConstructor
    area: VdomConstructor
    article: VdomConstructor
    aside: VdomConstructor
    audio: VdomConstructor
    b: VdomConstructor
    body: VdomConstructor
    base: VdomConstructor
    bdi: VdomConstructor
    bdo: VdomConstructor
    blockquote: VdomConstructor
    br: VdomConstructor
    button: VdomConstructor
    canvas: VdomConstructor
    caption: VdomConstructor
    cite: VdomConstructor
    code: VdomConstructor
    col: VdomConstructor
    colgroup: VdomConstructor
    data: VdomConstructor
    dd: VdomConstructor
    del_: VdomConstructor
    details: VdomConstructor
    dialog: VdomConstructor
    div: VdomConstructor
    dl: VdomConstructor
    dt: VdomConstructor
    em: VdomConstructor
    embed: VdomConstructor
    fieldset: VdomConstructor
    figcaption: VdomConstructor
    figure: VdomConstructor
    footer: VdomConstructor
    form: VdomConstructor
    h1: VdomConstructor
    h2: VdomConstructor
    h3: VdomConstructor
    h4: VdomConstructor
    h5: VdomConstructor
    h6: VdomConstructor
    head: VdomConstructor
    header: VdomConstructor
    hr: VdomConstructor
    html: VdomConstructor
    i: VdomConstructor
    iframe: VdomConstructor
    img: VdomConstructor
    input: VdomConstructor
    ins: VdomConstructor
    kbd: VdomConstructor
    label: VdomConstructor
    legend: VdomConstructor
    li: VdomConstructor
    link: VdomConstructor
    main: VdomConstructor
    map: VdomConstructor
    mark: VdomConstructor
    math: VdomConstructor
    menu: VdomConstructor
    menuitem: VdomConstructor
    meta: VdomConstructor
    meter: VdomConstructor
    nav: VdomConstructor
    noscript: VdomConstructor
    object: VdomConstructor
    ol: VdomConstructor
    option: VdomConstructor
    output: VdomConstructor
    p: VdomConstructor
    param: VdomConstructor
    picture: VdomConstructor
    portal: VdomConstructor
    pre: VdomConstructor
    progress: VdomConstructor
    q: VdomConstructor
    rp: VdomConstructor
    rt: VdomConstructor
    ruby: VdomConstructor
    s: VdomConstructor
    samp: VdomConstructor
    script: VdomConstructor
    section: VdomConstructor
    select: VdomConstructor
    slot: VdomConstructor
    small: VdomConstructor
    source: VdomConstructor
    span: VdomConstructor
    strong: VdomConstructor
    style: VdomConstructor
    sub: VdomConstructor
    summary: VdomConstructor
    sup: VdomConstructor
    table: VdomConstructor
    tbody: VdomConstructor
    td: VdomConstructor
    template: VdomConstructor
    textarea: VdomConstructor
    tfoot: VdomConstructor
    th: VdomConstructor
    thead: VdomConstructor
    time: VdomConstructor
    title: VdomConstructor
    tr: VdomConstructor
    track: VdomConstructor
    u: VdomConstructor
    ul: VdomConstructor
    var: VdomConstructor
    video: VdomConstructor
    wbr: VdomConstructor
    fragment: VdomConstructor

    # Special Case: SVG elements
    # Since SVG elements have a different set of allowed children, they are
    # separated into a different constructor, and are accessed via `html.svg.example()`
    svg: SvgConstructor


html = HtmlConstructor()
