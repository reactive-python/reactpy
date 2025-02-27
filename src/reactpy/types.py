from __future__ import annotations

from collections.abc import Awaitable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Protocol,
    TypeVar,
    overload,
    runtime_checkable,
)

from typing_extensions import NamedTuple, NotRequired, TypeAlias, TypedDict, Unpack

CarrierType = TypeVar("CarrierType")
_Type = TypeVar("_Type")


class State(NamedTuple, Generic[_Type]):
    value: _Type
    set_value: Callable[[_Type | Callable[[_Type], _Type]], None]


ComponentConstructor = Callable[..., "ComponentType"]
"""Simple function returning a new component"""

RootComponentConstructor = Callable[[], "ComponentType"]
"""The root component should be constructed by a function accepting no arguments."""


Key: TypeAlias = str | int


@runtime_checkable
class ComponentType(Protocol):
    """The expected interface for all component-like objects"""

    key: Key | None
    """An identifier which is unique amongst a component's immediate siblings"""

    type: Any
    """The function or class defining the behavior of this component

    This is used to see if two component instances share the same definition.
    """

    def render(self) -> VdomDict | ComponentType | str | None:
        """Render the component's view model."""


_Render_co = TypeVar("_Render_co", covariant=True)
_Event_contra = TypeVar("_Event_contra", contravariant=True)


@runtime_checkable
class LayoutType(Protocol[_Render_co, _Event_contra]):
    """Renders and delivers, updates to views and events to handlers, respectively"""

    async def render(
        self,
    ) -> _Render_co: ...  # Render an update to a view

    async def deliver(
        self, event: _Event_contra
    ) -> None: ...  # Relay an event to its respective handler

    async def __aenter__(
        self,
    ) -> LayoutType[
        _Render_co, _Event_contra
    ]: ...  # Prepare the layout for its first render

    async def __aexit__(
        self,
        exc_type: type[Exception],
        exc_value: Exception,
        traceback: TracebackType,
    ) -> bool | None:
        """Clean up the view after its final render"""


class CssStyleTypeDict(TypedDict, total=False):
    # TODO: This could generated by parsing from `csstype` in the future
    # https://www.npmjs.com/package/csstype
    accentColor: str | int
    alignContent: str | int
    alignItems: str | int
    alignSelf: str | int
    alignTracks: str | int
    all: str | int
    animation: str | int
    animationComposition: str | int
    animationDelay: str | int
    animationDirection: str | int
    animationDuration: str | int
    animationFillMode: str | int
    animationIterationCount: str | int
    animationName: str | int
    animationPlayState: str | int
    animationTimeline: str | int
    animationTimingFunction: str | int
    appearance: str | int
    aspectRatio: str | int
    backdropFilter: str | int
    backfaceVisibility: str | int
    background: str | int
    backgroundAttachment: str | int
    backgroundBlendMode: str | int
    backgroundClip: str | int
    backgroundColor: str | int
    backgroundImage: str | int
    backgroundOrigin: str | int
    backgroundPosition: str | int
    backgroundPositionX: str | int
    backgroundPositionY: str | int
    backgroundRepeat: str | int
    backgroundSize: str | int
    blockOverflow: str | int
    blockSize: str | int
    border: str | int
    borderBlock: str | int
    borderBlockColor: str | int
    borderBlockEnd: str | int
    borderBlockEndColor: str | int
    borderBlockEndStyle: str | int
    borderBlockEndWidth: str | int
    borderBlockStart: str | int
    borderBlockStartColor: str | int
    borderBlockStartStyle: str | int
    borderBlockStartWidth: str | int
    borderBlockStyle: str | int
    borderBlockWidth: str | int
    borderBottom: str | int
    borderBottomColor: str | int
    borderBottomLeftRadius: str | int
    borderBottomRightRadius: str | int
    borderBottomStyle: str | int
    borderBottomWidth: str | int
    borderCollapse: str | int
    borderColor: str | int
    borderEndEndRadius: str | int
    borderEndStartRadius: str | int
    borderImage: str | int
    borderImageOutset: str | int
    borderImageRepeat: str | int
    borderImageSlice: str | int
    borderImageSource: str | int
    borderImageWidth: str | int
    borderInline: str | int
    borderInlineColor: str | int
    borderInlineEnd: str | int
    borderInlineEndColor: str | int
    borderInlineEndStyle: str | int
    borderInlineEndWidth: str | int
    borderInlineStart: str | int
    borderInlineStartColor: str | int
    borderInlineStartStyle: str | int
    borderInlineStartWidth: str | int
    borderInlineStyle: str | int
    borderInlineWidth: str | int
    borderLeft: str | int
    borderLeftColor: str | int
    borderLeftStyle: str | int
    borderLeftWidth: str | int
    borderRadius: str | int
    borderRight: str | int
    borderRightColor: str | int
    borderRightStyle: str | int
    borderRightWidth: str | int
    borderSpacing: str | int
    borderStartEndRadius: str | int
    borderStartStartRadius: str | int
    borderStyle: str | int
    borderTop: str | int
    borderTopColor: str | int
    borderTopLeftRadius: str | int
    borderTopRightRadius: str | int
    borderTopStyle: str | int
    borderTopWidth: str | int
    borderWidth: str | int
    bottom: str | int
    boxDecorationBreak: str | int
    boxShadow: str | int
    boxSizing: str | int
    breakAfter: str | int
    breakBefore: str | int
    breakInside: str | int
    captionSide: str | int
    caret: str | int
    caretColor: str | int
    caretShape: str | int
    clear: str | int
    clip: str | int
    clipPath: str | int
    color: str | int
    colorScheme: str | int
    columnCount: str | int
    columnFill: str | int
    columnGap: str | int
    columnRule: str | int
    columnRuleColor: str | int
    columnRuleStyle: str | int
    columnRuleWidth: str | int
    columnSpan: str | int
    columnWidth: str | int
    columns: str | int
    contain: str | int
    containIntrinsicBlockSize: str | int
    containIntrinsicHeight: str | int
    containIntrinsicInlineSize: str | int
    containIntrinsicSize: str | int
    containIntrinsicWidth: str | int
    content: str | int
    contentVisibility: str | int
    counterIncrement: str | int
    counterReset: str | int
    counterSet: str | int
    cursor: str | int
    direction: str | int
    display: str | int
    emptyCells: str | int
    filter: str | int
    flex: str | int
    flexBasis: str | int
    flexDirection: str | int
    flexFlow: str | int
    flexGrow: str | int
    flexShrink: str | int
    flexWrap: str | int
    float: str | int
    font: str | int
    fontFamily: str | int
    fontFeatureSettings: str | int
    fontKerning: str | int
    fontLanguageOverride: str | int
    fontOpticalSizing: str | int
    fontSize: str | int
    fontSizeAdjust: str | int
    fontStretch: str | int
    fontStyle: str | int
    fontSynthesis: str | int
    fontVariant: str | int
    fontVariantAlternates: str | int
    fontVariantCaps: str | int
    fontVariantEastAsian: str | int
    fontVariantLigatures: str | int
    fontVariantNumeric: str | int
    fontVariantPosition: str | int
    fontVariationSettings: str | int
    fontWeight: str | int
    forcedColorAdjust: str | int
    gap: str | int
    grid: str | int
    gridArea: str | int
    gridAutoColumns: str | int
    gridAutoFlow: str | int
    gridAutoRows: str | int
    gridColumn: str | int
    gridColumnEnd: str | int
    gridColumnStart: str | int
    gridRow: str | int
    gridRowEnd: str | int
    gridRowStart: str | int
    gridTemplate: str | int
    gridTemplateAreas: str | int
    gridTemplateColumns: str | int
    gridTemplateRows: str | int
    hangingPunctuation: str | int
    height: str | int
    hyphenateCharacter: str | int
    hyphenateLimitChars: str | int
    hyphens: str | int
    imageOrientation: str | int
    imageRendering: str | int
    imageResolution: str | int
    inherit: str | int
    initial: str | int
    initialLetter: str | int
    initialLetterAlign: str | int
    inlineSize: str | int
    inputSecurity: str | int
    inset: str | int
    insetBlock: str | int
    insetBlockEnd: str | int
    insetBlockStart: str | int
    insetInline: str | int
    insetInlineEnd: str | int
    insetInlineStart: str | int
    isolation: str | int
    justifyContent: str | int
    justifyItems: str | int
    justifySelf: str | int
    justifyTracks: str | int
    left: str | int
    letterSpacing: str | int
    lineBreak: str | int
    lineClamp: str | int
    lineHeight: str | int
    lineHeightStep: str | int
    listStyle: str | int
    listStyleImage: str | int
    listStylePosition: str | int
    listStyleType: str | int
    margin: str | int
    marginBlock: str | int
    marginBlockEnd: str | int
    marginBlockStart: str | int
    marginBottom: str | int
    marginInline: str | int
    marginInlineEnd: str | int
    marginInlineStart: str | int
    marginLeft: str | int
    marginRight: str | int
    marginTop: str | int
    marginTrim: str | int
    mask: str | int
    maskBorder: str | int
    maskBorderMode: str | int
    maskBorderOutset: str | int
    maskBorderRepeat: str | int
    maskBorderSlice: str | int
    maskBorderSource: str | int
    maskBorderWidth: str | int
    maskClip: str | int
    maskComposite: str | int
    maskImage: str | int
    maskMode: str | int
    maskOrigin: str | int
    maskPosition: str | int
    maskRepeat: str | int
    maskSize: str | int
    maskType: str | int
    masonryAutoFlow: str | int
    mathDepth: str | int
    mathShift: str | int
    mathStyle: str | int
    maxBlockSize: str | int
    maxHeight: str | int
    maxInlineSize: str | int
    maxLines: str | int
    maxWidth: str | int
    minBlockSize: str | int
    minHeight: str | int
    minInlineSize: str | int
    minWidth: str | int
    mixBlendMode: str | int
    objectFit: str | int
    objectPosition: str | int
    offset: str | int
    offsetAnchor: str | int
    offsetDistance: str | int
    offsetPath: str | int
    offsetPosition: str | int
    offsetRotate: str | int
    opacity: str | int
    order: str | int
    orphans: str | int
    outline: str | int
    outlineColor: str | int
    outlineOffset: str | int
    outlineStyle: str | int
    outlineWidth: str | int
    overflow: str | int
    overflowAnchor: str | int
    overflowBlock: str | int
    overflowClipMargin: str | int
    overflowInline: str | int
    overflowWrap: str | int
    overflowX: str | int
    overflowY: str | int
    overscrollBehavior: str | int
    overscrollBehaviorBlock: str | int
    overscrollBehaviorInline: str | int
    overscrollBehaviorX: str | int
    overscrollBehaviorY: str | int
    padding: str | int
    paddingBlock: str | int
    paddingBlockEnd: str | int
    paddingBlockStart: str | int
    paddingBottom: str | int
    paddingInline: str | int
    paddingInlineEnd: str | int
    paddingInlineStart: str | int
    paddingLeft: str | int
    paddingRight: str | int
    paddingTop: str | int
    pageBreakAfter: str | int
    pageBreakBefore: str | int
    pageBreakInside: str | int
    paintOrder: str | int
    perspective: str | int
    perspectiveOrigin: str | int
    placeContent: str | int
    placeItems: str | int
    placeSelf: str | int
    pointerEvents: str | int
    position: str | int
    printColorAdjust: str | int
    quotes: str | int
    resize: str | int
    revert: str | int
    right: str | int
    rotate: str | int
    rowGap: str | int
    rubyAlign: str | int
    rubyMerge: str | int
    rubyPosition: str | int
    scale: str | int
    scrollBehavior: str | int
    scrollMargin: str | int
    scrollMarginBlock: str | int
    scrollMarginBlockEnd: str | int
    scrollMarginBlockStart: str | int
    scrollMarginBottom: str | int
    scrollMarginInline: str | int
    scrollMarginInlineEnd: str | int
    scrollMarginInlineStart: str | int
    scrollMarginLeft: str | int
    scrollMarginRight: str | int
    scrollMarginTop: str | int
    scrollPadding: str | int
    scrollPaddingBlock: str | int
    scrollPaddingBlockEnd: str | int
    scrollPaddingBlockStart: str | int
    scrollPaddingBottom: str | int
    scrollPaddingInline: str | int
    scrollPaddingInlineEnd: str | int
    scrollPaddingInlineStart: str | int
    scrollPaddingLeft: str | int
    scrollPaddingRight: str | int
    scrollPaddingTop: str | int
    scrollSnapAlign: str | int
    scrollSnapStop: str | int
    scrollSnapType: str | int
    scrollTimeline: str | int
    scrollTimelineAxis: str | int
    scrollTimelineName: str | int
    scrollbarColor: str | int
    scrollbarGutter: str | int
    scrollbarWidth: str | int
    shapeImageThreshold: str | int
    shapeMargin: str | int
    shapeOutside: str | int
    tabSize: str | int
    tableLayout: str | int
    textAlign: str | int
    textAlignLast: str | int
    textCombineUpright: str | int
    textDecoration: str | int
    textDecorationColor: str | int
    textDecorationLine: str | int
    textDecorationSkip: str | int
    textDecorationSkipInk: str | int
    textDecorationStyle: str | int
    textDecorationThickness: str | int
    textEmphasis: str | int
    textEmphasisColor: str | int
    textEmphasisPosition: str | int
    textEmphasisStyle: str | int
    textIndent: str | int
    textJustify: str | int
    textOrientation: str | int
    textOverflow: str | int
    textRendering: str | int
    textShadow: str | int
    textSizeAdjust: str | int
    textTransform: str | int
    textUnderlineOffset: str | int
    textUnderlinePosition: str | int
    top: str | int
    touchAction: str | int
    transform: str | int
    transformBox: str | int
    transformOrigin: str | int
    transformStyle: str | int
    transition: str | int
    transitionDelay: str | int
    transitionDuration: str | int
    transitionProperty: str | int
    transitionTimingFunction: str | int
    translate: str | int
    unicodeBidi: str | int
    unset: str | int
    userSelect: str | int
    verticalAlign: str | int
    visibility: str | int
    whiteSpace: str | int
    widows: str | int
    width: str | int
    willChange: str | int
    wordBreak: str | int
    wordSpacing: str | int
    wordWrap: str | int
    writingMode: str | int
    zIndex: str | int


# TODO: Enable `extra_items` on `CssStyleDict` when PEP 728 is merged, likely in Python 3.14. Ref: https://peps.python.org/pep-0728/
CssStyleDict = CssStyleTypeDict | dict[str, Any]

EventFunc = Callable[[dict[str, Any]], Awaitable[None] | None]


class DangerouslySetInnerHTML(TypedDict):
    __html: str


# TODO: It's probably better to break this one attributes dict down into what each specific
# HTML node's attributes can be, and make sure those types are resolved correctly within `HtmlConstructor`
# TODO: This could be generated by parsing from `@types/react` in the future
# https://www.npmjs.com/package/@types/react?activeTab=code
VdomAttributesTypeDict = TypedDict(
    "VdomAttributesTypeDict",
    {
        "key": Key,
        "value": Any,
        "defaultValue": Any,
        "dangerouslySetInnerHTML": DangerouslySetInnerHTML,
        "suppressContentEditableWarning": bool,
        "suppressHydrationWarning": bool,
        "style": CssStyleDict,
        "accessKey": str,
        "aria-": None,
        "autoCapitalize": str,
        "className": str,
        "contentEditable": bool,
        "data-": None,
        "dir": Literal["ltr", "rtl"],
        "draggable": bool,
        "enterKeyHint": str,
        "htmlFor": str,
        "hidden": bool | str,
        "id": str,
        "is": str,
        "inputMode": str,
        "itemProp": str,
        "lang": str,
        "onAnimationEnd": EventFunc,
        "onAnimationEndCapture": EventFunc,
        "onAnimationIteration": EventFunc,
        "onAnimationIterationCapture": EventFunc,
        "onAnimationStart": EventFunc,
        "onAnimationStartCapture": EventFunc,
        "onAuxClick": EventFunc,
        "onAuxClickCapture": EventFunc,
        "onBeforeInput": EventFunc,
        "onBeforeInputCapture": EventFunc,
        "onBlur": EventFunc,
        "onBlurCapture": EventFunc,
        "onClick": EventFunc,
        "onClickCapture": EventFunc,
        "onCompositionStart": EventFunc,
        "onCompositionStartCapture": EventFunc,
        "onCompositionEnd": EventFunc,
        "onCompositionEndCapture": EventFunc,
        "onCompositionUpdate": EventFunc,
        "onCompositionUpdateCapture": EventFunc,
        "onContextMenu": EventFunc,
        "onContextMenuCapture": EventFunc,
        "onCopy": EventFunc,
        "onCopyCapture": EventFunc,
        "onCut": EventFunc,
        "onCutCapture": EventFunc,
        "onDoubleClick": EventFunc,
        "onDoubleClickCapture": EventFunc,
        "onDrag": EventFunc,
        "onDragCapture": EventFunc,
        "onDragEnd": EventFunc,
        "onDragEndCapture": EventFunc,
        "onDragEnter": EventFunc,
        "onDragEnterCapture": EventFunc,
        "onDragOver": EventFunc,
        "onDragOverCapture": EventFunc,
        "onDragStart": EventFunc,
        "onDragStartCapture": EventFunc,
        "onDrop": EventFunc,
        "onDropCapture": EventFunc,
        "onFocus": EventFunc,
        "onFocusCapture": EventFunc,
        "onGotPointerCapture": EventFunc,
        "onGotPointerCaptureCapture": EventFunc,
        "onKeyDown": EventFunc,
        "onKeyDownCapture": EventFunc,
        "onKeyPress": EventFunc,
        "onKeyPressCapture": EventFunc,
        "onKeyUp": EventFunc,
        "onKeyUpCapture": EventFunc,
        "onLostPointerCapture": EventFunc,
        "onLostPointerCaptureCapture": EventFunc,
        "onMouseDown": EventFunc,
        "onMouseDownCapture": EventFunc,
        "onMouseEnter": EventFunc,
        "onMouseLeave": EventFunc,
        "onMouseMove": EventFunc,
        "onMouseMoveCapture": EventFunc,
        "onMouseOut": EventFunc,
        "onMouseOutCapture": EventFunc,
        "onMouseUp": EventFunc,
        "onMouseUpCapture": EventFunc,
        "onPointerCancel": EventFunc,
        "onPointerCancelCapture": EventFunc,
        "onPointerDown": EventFunc,
        "onPointerDownCapture": EventFunc,
        "onPointerEnter": EventFunc,
        "onPointerLeave": EventFunc,
        "onPointerMove": EventFunc,
        "onPointerMoveCapture": EventFunc,
        "onPointerOut": EventFunc,
        "onPointerOutCapture": EventFunc,
        "onPointerUp": EventFunc,
        "onPointerUpCapture": EventFunc,
        "onPaste": EventFunc,
        "onPasteCapture": EventFunc,
        "onScroll": EventFunc,
        "onScrollCapture": EventFunc,
        "onSelect": EventFunc,
        "onSelectCapture": EventFunc,
        "onTouchCancel": EventFunc,
        "onTouchCancelCapture": EventFunc,
        "onTouchEnd": EventFunc,
        "onTouchEndCapture": EventFunc,
        "onTouchMove": EventFunc,
        "onTouchMoveCapture": EventFunc,
        "onTouchStart": EventFunc,
        "onTouchStartCapture": EventFunc,
        "onTransitionEnd": EventFunc,
        "onTransitionEndCapture": EventFunc,
        "onWheel": EventFunc,
        "onWheelCapture": EventFunc,
        "role": str,
        "slot": str,
        "spellCheck": bool | None,
        "tabIndex": int,
        "title": str,
        "translate": Literal["yes", "no"],
        "onReset": EventFunc,
        "onResetCapture": EventFunc,
        "onSubmit": EventFunc,
        "onSubmitCapture": EventFunc,
        "formAction": str | Callable,
        "checked": bool,
        "defaultChecked": bool,
        "accept": str,
        "alt": str,
        "capture": str,
        "autoComplete": str,
        "autoFocus": bool,
        "dirname": str,
        "disabled": bool,
        "form": str,
        "formEnctype": str,
        "formMethod": str,
        "formNoValidate": str,
        "formTarget": str,
        "height": str,
        "list": str,
        "max": int,
        "maxLength": int,
        "min": int,
        "minLength": int,
        "multiple": bool,
        "name": str,
        "onChange": EventFunc,
        "onChangeCapture": EventFunc,
        "onInput": EventFunc,
        "onInputCapture": EventFunc,
        "onInvalid": EventFunc,
        "onInvalidCapture": EventFunc,
        "pattern": str,
        "placeholder": str,
        "readOnly": bool,
        "required": bool,
        "size": int,
        "src": str,
        "step": int | Literal["any"],
        "type": str,
        "width": str,
        "label": str,
        "cols": int,
        "rows": int,
        "wrap": Literal["hard", "soft", "off"],
        "rel": str,
        "precedence": str,
        "media": str,
        "onError": EventFunc,
        "onLoad": EventFunc,
        "as": str,
        "imageSrcSet": str,
        "imageSizes": str,
        "sizes": str,
        "href": str,
        "crossOrigin": str,
        "referrerPolicy": str,
        "fetchPriority": str,
        "hrefLang": str,
        "integrity": str,
        "blocking": str,
        "async": bool,
        "noModule": bool,
        "nonce": str,
        "referrer": str,
        "defer": str,
        "onToggle": EventFunc,
        "onToggleCapture": EventFunc,
        "onLoadCapture": EventFunc,
        "onErrorCapture": EventFunc,
        "onAbort": EventFunc,
        "onAbortCapture": EventFunc,
        "onCanPlay": EventFunc,
        "onCanPlayCapture": EventFunc,
        "onCanPlayThrough": EventFunc,
        "onCanPlayThroughCapture": EventFunc,
        "onDurationChange": EventFunc,
        "onDurationChangeCapture": EventFunc,
        "onEmptied": EventFunc,
        "onEmptiedCapture": EventFunc,
        "onEncrypted": EventFunc,
        "onEncryptedCapture": EventFunc,
        "onEnded": EventFunc,
        "onEndedCapture": EventFunc,
        "onLoadedData": EventFunc,
        "onLoadedDataCapture": EventFunc,
        "onLoadedMetadata": EventFunc,
        "onLoadedMetadataCapture": EventFunc,
        "onLoadStart": EventFunc,
        "onLoadStartCapture": EventFunc,
        "onPause": EventFunc,
        "onPauseCapture": EventFunc,
        "onPlay": EventFunc,
        "onPlayCapture": EventFunc,
        "onPlaying": EventFunc,
        "onPlayingCapture": EventFunc,
        "onProgress": EventFunc,
        "onProgressCapture": EventFunc,
        "onRateChange": EventFunc,
        "onRateChangeCapture": EventFunc,
        "onResize": EventFunc,
        "onResizeCapture": EventFunc,
        "onSeeked": EventFunc,
        "onSeekedCapture": EventFunc,
        "onSeeking": EventFunc,
        "onSeekingCapture": EventFunc,
        "onStalled": EventFunc,
        "onStalledCapture": EventFunc,
        "onSuspend": EventFunc,
        "onSuspendCapture": EventFunc,
        "onTimeUpdate": EventFunc,
        "onTimeUpdateCapture": EventFunc,
        "onVolumeChange": EventFunc,
        "onVolumeChangeCapture": EventFunc,
        "onWaiting": EventFunc,
        "onWaitingCapture": EventFunc,
    },
    total=False,
)

# TODO: Enable `extra_items` on `VdomAttributes` when PEP 728 is merged, likely in Python 3.14. Ref: https://peps.python.org/pep-0728/
VdomAttributes = VdomAttributesTypeDict | dict[str, Any]

VdomDictKeys = Literal[
    "tagName",
    "key",
    "children",
    "attributes",
    "eventHandlers",
    "importSource",
]
ALLOWED_VDOM_KEYS = {
    "tagName",
    "key",
    "children",
    "attributes",
    "eventHandlers",
    "importSource",
}


class VdomTypeDict(TypedDict):
    """TypedDict representation of what the `VdomDict` should look like."""

    tagName: str
    key: NotRequired[Key | None]
    children: NotRequired[Sequence[ComponentType | VdomChild]]
    attributes: NotRequired[VdomAttributes]
    eventHandlers: NotRequired[EventHandlerDict]
    importSource: NotRequired[ImportSourceDict]


class VdomDict(dict):
    """A light wrapper around Python `dict` that represents a Virtual DOM element."""

    def __init__(self, **kwargs: Unpack[VdomTypeDict]) -> None:
        if "tagName" not in kwargs:
            msg = "VdomDict requires a 'tagName' key."
            raise ValueError(msg)
        invalid_keys = set(kwargs) - ALLOWED_VDOM_KEYS
        if invalid_keys:
            msg = f"Invalid keys: {invalid_keys}."
            raise ValueError(msg)

        super().__init__(**kwargs)

    @overload
    def __getitem__(self, key: Literal["tagName"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["key"]) -> Key | None: ...
    @overload
    def __getitem__(
        self, key: Literal["children"]
    ) -> Sequence[ComponentType | VdomChild]: ...
    @overload
    def __getitem__(self, key: Literal["attributes"]) -> VdomAttributes: ...
    @overload
    def __getitem__(self, key: Literal["eventHandlers"]) -> EventHandlerDict: ...
    @overload
    def __getitem__(self, key: Literal["importSource"]) -> ImportSourceDict: ...
    def __getitem__(self, key: VdomDictKeys) -> Any:
        return super().__getitem__(key)

    @overload
    def __setitem__(self, key: Literal["tagName"], value: str) -> None: ...
    @overload
    def __setitem__(self, key: Literal["key"], value: Key | None) -> None: ...
    @overload
    def __setitem__(
        self, key: Literal["children"], value: Sequence[ComponentType | VdomChild]
    ) -> None: ...
    @overload
    def __setitem__(
        self, key: Literal["attributes"], value: VdomAttributes
    ) -> None: ...
    @overload
    def __setitem__(
        self, key: Literal["eventHandlers"], value: EventHandlerDict
    ) -> None: ...
    @overload
    def __setitem__(
        self, key: Literal["importSource"], value: ImportSourceDict
    ) -> None: ...
    def __setitem__(self, key: VdomDictKeys, value: Any) -> None:
        if key not in ALLOWED_VDOM_KEYS:
            raise KeyError(f"Invalid key: {key}")
        super().__setitem__(key, value)


VdomChild: TypeAlias = ComponentType | VdomDict | str | None | Any
"""A single child element of a :class:`VdomDict`"""

VdomChildren: TypeAlias = Sequence[VdomChild] | VdomChild
"""Describes a series of :class:`VdomChild` elements"""


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any
    sourceType: str
    unmountBeforeUpdate: bool


class VdomJson(TypedDict):
    """A JSON serializable form of :class:`VdomDict` matching the :data:`VDOM_JSON_SCHEMA`"""

    tagName: str
    key: NotRequired[Key]
    error: NotRequired[str]
    children: NotRequired[list[Any]]
    attributes: NotRequired[VdomAttributes]
    eventHandlers: NotRequired[dict[str, JsonEventTarget]]
    importSource: NotRequired[JsonImportSource]


class JsonEventTarget(TypedDict):
    target: str
    preventDefault: bool
    stopPropagation: bool


class JsonImportSource(TypedDict):
    source: str
    fallback: Any


class EventHandlerFunc(Protocol):
    """A coroutine which can handle event data"""

    async def __call__(self, data: Sequence[Any]) -> None: ...


@runtime_checkable
class EventHandlerType(Protocol):
    """Defines a handler for some event"""

    prevent_default: bool
    """Whether to block the event from propagating further up the DOM"""

    stop_propagation: bool
    """Stops the default action associate with the event from taking place."""

    function: EventHandlerFunc
    """A coroutine which can respond to an event and its data"""

    target: str | None
    """Typically left as ``None`` except when a static target is useful.

    When testing, it may be useful to specify a static target ID so events can be
    triggered programmatically.

    .. note::

        When ``None``, it is left to a :class:`LayoutType` to auto generate a unique ID.
    """


EventHandlerMapping = Mapping[str, EventHandlerType]
"""A generic mapping between event names to their handlers"""

EventHandlerDict: TypeAlias = dict[str, EventHandlerType]
"""A dict mapping between event names to their handlers"""


class VdomConstructor(Protocol):
    """Standard function for constructing a :class:`VdomDict`"""

    @overload
    def __call__(
        self, attributes: VdomAttributes, /, *children: VdomChildren
    ) -> VdomDict: ...

    @overload
    def __call__(self, *children: VdomChildren) -> VdomDict: ...

    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict: ...


class LayoutUpdateMessage(TypedDict):
    """A message describing an update to a layout"""

    type: Literal["layout-update"]
    """The type of message"""
    path: str
    """JSON Pointer path to the model element being updated"""
    model: VdomJson | dict[str, Any]
    """The model to assign at the given JSON Pointer path"""


class LayoutEventMessage(TypedDict):
    """Message describing an event originating from an element in the layout"""

    type: Literal["layout-event"]
    """The type of message"""
    target: str
    """The ID of the event handler."""
    data: Sequence[Any]
    """A list of event data passed to the event handler."""


class Context(Protocol[_Type]):
    """Returns a :class:`ContextProvider` component"""

    def __call__(
        self,
        *children: Any,
        value: _Type = ...,
        key: Key | None = ...,
    ) -> ContextProviderType[_Type]: ...


class ContextProviderType(ComponentType, Protocol[_Type]):
    """A component which provides a context value to its children"""

    type: Context[_Type]
    """The context type"""

    @property
    def value(self) -> _Type: ...  # Current context value


@dataclass
class Connection(Generic[CarrierType]):
    """Represents a connection with a client"""

    scope: dict[str, Any]
    """A scope dictionary related to the current connection."""

    location: Location
    """The current location (URL)"""

    carrier: CarrierType
    """How the connection is mediated. For example, a request or websocket.

    This typically depends on the backend implementation.
    """


@dataclass
class Location:
    """Represents the current location (URL)

    Analogous to, but not necessarily identical to, the client-side
    ``document.location`` object.
    """

    path: str
    """The URL's path segment. This typically represents the current
    HTTP request's path."""

    query_string: str
    """HTTP query string - a '?' followed by the parameters of the URL.

    If there are no search parameters this should be an empty string
    """


class ReactPyConfig(TypedDict, total=False):
    path_prefix: str
    web_modules_dir: Path
    reconnect_interval: int
    reconnect_max_interval: int
    reconnect_max_retries: int
    reconnect_backoff_multiplier: float
    async_rendering: bool
    debug: bool
    tests_default_timeout: int


class PyScriptOptions(TypedDict, total=False):
    extra_py: Sequence[str]
    extra_js: dict[str, Any] | str
    config: dict[str, Any] | str


class CustomVdomConstructor(Protocol):
    def __call__(
        self,
        attributes: VdomAttributes,
        children: Sequence[VdomChildren],
        key: Key | None,
        event_handlers: EventHandlerDict,
    ) -> VdomDict: ...


class EllipsisRepr:
    def __repr__(self) -> str:
        return "..."
