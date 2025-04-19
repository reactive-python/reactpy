from __future__ import annotations

from typing import Any, cast

from reactpy.core.events import EventHandler, to_event_handler_function
from reactpy.types import VdomAttributes, VdomDict


def attributes_to_reactjs(attributes: VdomAttributes):
    """Convert HTML attribute names to their ReactJS equivalents."""
    attrs = cast(VdomAttributes, attributes.items())
    attrs = cast(
        VdomAttributes,
        {REACT_PROP_SUBSTITUTIONS.get(k, k): v for k, v in attrs},
    )
    return attrs


class RequiredTransforms:
    """Performs any necessary transformations related to `string_to_reactpy` to automatically prevent
    issues with React's rendering engine.
    """

    def __init__(self, vdom: VdomDict, intercept_links: bool = True) -> None:
        self._intercept_links = intercept_links

        # Run every transform in this class.
        for name in dir(self):
            # Any method that doesn't start with an underscore is assumed to be a transform.
            if not name.startswith("_"):
                getattr(self, name)(vdom)

    def normalize_style_attributes(self, vdom: dict[str, Any]) -> None:
        """Convert style attribute from str -> dict with camelCase keys"""
        if (
            "attributes" in vdom
            and "style" in vdom["attributes"]
            and isinstance(vdom["attributes"]["style"], str)
        ):
            vdom["attributes"]["style"] = {
                self._kebab_to_camel_case(key.strip()): value.strip()
                for key, value in (
                    part.split(":", 1)
                    for part in vdom["attributes"]["style"].split(";")
                    if ":" in part
                )
            }

    @staticmethod
    def textarea_children_to_prop(vdom: VdomDict) -> None:
        """Transformation that converts the text content of a <textarea> to a ReactJS prop."""
        if vdom["tagName"] == "textarea" and "children" in vdom and vdom["children"]:
            text_content = vdom.pop("children")
            text_content = "".join(
                [child for child in text_content if isinstance(child, str)]
            )

            vdom.setdefault("attributes", {})
            if "attributes" in vdom:
                default_value = vdom["attributes"].pop("defaultValue", "")
                vdom["attributes"]["defaultValue"] = text_content or default_value

    def select_element_to_reactjs(self, vdom: VdomDict) -> None:
        """Performs several transformations on the <select> element to make it ReactJS-compatible.

        1. Convert the `selected` attribute on <option> is replaced with the ReactJS equivalent.
            Namely, ReactJS uses props on the parent <select> element to indicate which <option> is selected.
        2. Sets the `value` prop on each <option> element so that ReactJS knows the identity of each element."""
        if vdom["tagName"] != "select" or "children" not in vdom:
            return

        vdom.setdefault("attributes", {})
        if "attributes" in vdom:
            multiple_choice = vdom["attributes"].get("multiple") is not None
            selected_options = self._parse_options(vdom)
            if multiple_choice:
                vdom["attributes"]["multiple"] = True
            if selected_options and not multiple_choice:
                vdom["attributes"]["defaultValue"] = selected_options[0]
            if selected_options and multiple_choice:
                vdom["attributes"]["defaultValue"] = selected_options

    @staticmethod
    def input_element_value_prop_to_defaultValue(vdom: VdomDict) -> None:
        """ReactJS will complain that inputs are uncontrolled if defining the `value` prop,
        so we use `defaultValue` instead. This has an added benefit of not deleting/overriding
        any user input when a `string_to_reactpy` re-renders fields that do not retain their `value`,
        such as password fields."""
        if vdom["tagName"] != "input":
            return

        vdom.setdefault("attributes", {})
        if "attributes" in vdom:
            value = vdom["attributes"].pop("value", None)
            if value is not None:
                vdom["attributes"]["defaultValue"] = value

    @staticmethod
    def infer_key_from_attributes(vdom: VdomDict) -> None:
        """Infer the ReactJS `key` by looking at any attributes that should be unique."""
        attributes = vdom.get("attributes", {})
        if not attributes:
            return

        # Infer 'key' from 'attributes.key'
        key = attributes.get("key", None)

        # Infer 'key' from 'attributes.id'
        if key is None:
            key = attributes.get("id")

        # Infer 'key' from 'attributes.name'
        if key is None and vdom["tagName"] in {"input", "select", "textarea"}:
            key = attributes.get("name")

        if key:
            vdom["key"] = key

    def intercept_link_clicks(self, vdom: VdomDict) -> None:
        """Intercepts anchor link clicks and prevents the default behavior.
        This allows ReactPy-Router to handle the navigation instead of the browser."""
        if vdom["tagName"] != "a" or not self._intercept_links:
            return

        vdom.setdefault("eventHandlers", {})
        if "eventHandlers" in vdom and isinstance(vdom["eventHandlers"], dict):
            vdom["eventHandlers"]["onClick"] = EventHandler(
                to_event_handler_function(lambda *_args, **_kwargs: None),
                prevent_default=True,
            )

    def _parse_options(self, vdom_or_any: Any) -> list[str]:
        """Parses a tree of elements to find all <option> elements with the 'selected' prop.
        1. Sets the `value` prop on each <option> element so that ReactJS knows the identity of each element.
        2. The 'selected' prop is removed, and this function returns a list of selected elements."""

        # Since we recursively iterate through children, return early if the current node is not a dict.
        selected_options = []
        if not isinstance(vdom_or_any, dict):
            return selected_options

        vdom = vdom_or_any
        if vdom["tagName"] == "option" and "attributes" in vdom:
            value = vdom["attributes"].setdefault("value", vdom["children"][0])

            if "selected" in vdom["attributes"]:
                vdom["attributes"].pop("selected")
                selected_options.append(value)

        for child in vdom.get("children", []):
            selected_options.extend(self._parse_options(child))

        return selected_options

    @staticmethod
    def _kebab_to_camel_case(kebab_case: str) -> str:
        """Convert kebab-case to camelCase."""
        return "".join(
            part.capitalize() if i else part
            for i, part in enumerate(kebab_case.split("-"))
        )


KNOWN_REACT_PROPS = {
    "onLoadStart",
    "onTouchStart",
    "onProgressCapture",
    "contentEditable",
    "dir",
    "onClick",
    "onTimeUpdateCapture",
    "onPointerCancelCapture",
    "charset",
    "formEnctype",
    "accessKey",
    "required",
    "onError",
    "capture",
    "formAction",
    "onEmptiedCapture",
    "hrefLang",
    "form",
    "onKeyDownCapture",
    "onMouseUpCapture",
    "onBeforeInput",
    "onCutCapture",
    "onDurationChange",
    "onCanPlayCapture",
    "onGotPointerCapture",
    "onSuspend",
    "inputMode",
    "onPointerCancel",
    "onSuspendCapture",
    "onKeyDown",
    "onTimeUpdate",
    "maxLength",
    "onDropCapture",
    "onCompositionUpdateCapture",
    "nonce",
    "onKeyUp",
    "title",
    "onSeekingCapture",
    "onStalledCapture",
    "onKeyPressCapture",
    "referrerPolicy",
    "onMouseMove",
    "onPointerDown",
    "onReset",
    "onScrollCapture",
    "onEncryptedCapture",
    "onWaiting",
    "placeholder",
    "onCompositionUpdate",
    "onTouchEndCapture",
    "onLoadedMetadata",
    "onCanPlay",
    "onCopy",
    "onTouchMoveCapture",
    "onLoadCapture",
    "onMouseDownCapture",
    "pattern",
    "onCanPlayThrough",
    "onTransitionEnd",
    "min",
    "autoComplete",
    "referrer",
    "checked",
    "onWheelCapture",
    "autoFocus",
    "alt",
    "onTransitionEndCapture",
    "onPause",
    "onLoadedDataCapture",
    "onAuxClickCapture",
    "onDragStart",
    "onInputCapture",
    "onAbort",
    "onBlurCapture",
    "onTouchStartCapture",
    "onCompositionStartCapture",
    "onDrag",
    "max",
    "enterKeyHint",
    "onInput",
    "width",
    "accept",
    "onResetCapture",
    "onScroll",
    "suppressContentEditableWarning",
    "onKeyUpCapture",
    "onPaste",
    "onPauseCapture",
    "onTouchMove",
    "onDoubleClickCapture",
    "defaultChecked",
    "spellCheck",
    "onChangeCapture",
    "onBeforeInputCapture",
    "onInvalid",
    "fetchPriority",
    "onAnimationEndCapture",
    "onSeeked",
    "onToggle",
    "onPlayCapture",
    "onAnimationIteration",
    "onEndedCapture",
    "onPlaying",
    "multiple",
    "dangerouslySetInnerHTML",
    "as",
    "onLoadedMetadataCapture",
    "href",
    "draggable",
    "lang",
    "onAnimationEnd",
    "translate",
    "imageSrcSet",
    "onRateChange",
    "itemProp",
    "onPointerLeave",
    "onSelect",
    "onMouseOut",
    "dirname",
    "onMouseDown",
    "onPointerUp",
    "style",
    "onGotPointerCaptureCapture",
    "onLoadStartCapture",
    "formNoValidate",
    "className",
    "onClickCapture",
    "onFocusCapture",
    "onDragEnd",
    "is",
    "onPasteCapture",
    "onVolumeChange",
    "onDragOver",
    "onMouseOutCapture",
    "onCompositionStart",
    "onDragCapture",
    "onMouseEnter",
    "onFocus",
    "onLostPointerCapture",
    "onEmptied",
    "onMouseMoveCapture",
    "onBlur",
    "onContextMenuCapture",
    "wrap",
    "onChange",
    "onKeyPress",
    "onMouseUp",
    "onSubmit",
    "onTouchCancel",
    "integrity",
    "id",
    "onDragOverCapture",
    "minLength",
    "onTouchEnd",
    "onAuxClick",
    "onLoad",
    "content",
    "onCanPlayThroughCapture",
    "onAnimationStartCapture",
    "onAnimationStart",
    "onDragEnter",
    "onPointerDownCapture",
    "onEnded",
    "onProgress",
    "onDragEndCapture",
    "slot",
    "onRateChangeCapture",
    "onMouseLeave",
    "async",
    "height",
    "step",
    "disabled",
    "onLoadedData",
    "src",
    "onPointerEnter",
    "onTouchCancelCapture",
    "readOnly",
    "size",
    "suppressHydrationWarning",
    "htmlFor",
    "onPointerOutCapture",
    "onCopyCapture",
    "onDoubleClick",
    "onCompositionEnd",
    "onCompositionEndCapture",
    "onSeeking",
    "onPointerOut",
    "onSubmitCapture",
    "onSeekedCapture",
    "onEncrypted",
    "onLostPointerCaptureCapture",
    "onToggleCapture",
    "onPointerUpCapture",
    "onWheel",
    "onCut",
    "onAbortCapture",
    "onResizeCapture",
    "httpEquiv",
    "onResize",
    "type",
    "onVolumeChangeCapture",
    "onSelectCapture",
    "onDragStartCapture",
    "imageSizes",
    "crossOrigin",
    "autoCapitalize",
    "value",
    "list",
    "onInvalidCapture",
    "formTarget",
    "onAnimationIterationCapture",
    "onStalled",
    "onWaitingCapture",
    "cols",
    "onPointerMove",
    "onDragEnterCapture",
    "tabIndex",
    "onPlayingCapture",
    "rows",
    "role",
    "onPointerMoveCapture",
    "onContextMenu",
    "hidden",
    "noModule",
    "formMethod",
    "sizes",
    "onPlay",
    "onDurationChangeCapture",
    "onErrorCapture",
    "onDrop",
    "defaultValue",
    "name",
}

REACT_PROP_SUBSTITUTIONS = {prop.lower(): prop for prop in KNOWN_REACT_PROPS} | {
    "for": "htmlFor",
    "class": "className",
    "checked": "defaultChecked",
    "accept-charset": "acceptCharset",
    "http-equiv": "httpEquiv",
}
"""A mapping of HTML prop names to their ReactJS equivalents, where:
Key = HTML prop name
Value = Equivalent ReactJS prop name
"""
