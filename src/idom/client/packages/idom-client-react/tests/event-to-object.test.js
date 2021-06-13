import { test } from "uvu";
import * as assert from "uvu/assert";
import serializeEvent from "../src/event-to-object.js";
import "./tooling/setup.js";

const allTargetData = {
  files: [
    {
      lastModified: 0,
      name: "something",
      type: "some-type",
      size: 0,
    },
  ],
  value: "something",
  currentTime: 35,
  tagName: null, // overwritten in tests
};

[
  {
    case: "adds 'files' and 'value' attributes for INPUT if type=file",
    tagName: "INPUT",
    otherAttrs: { type: "file" },
    output: {
      files: allTargetData.files,
      value: allTargetData.value,
    },
  },
  ...["BUTTON", "INPUT", "OPTION", "LI", "METER", "PROGRESS", "PARAM"].map(
    (tagName) => ({
      case: `adds 'value' attribute for ${tagName} element`,
      tagName,
      output: { value: allTargetData.value },
    })
  ),
  ...["AUDIO", "VIDEO"].map((tagName) => ({
    case: `adds 'currentTime' attribute for ${tagName} element`,
    tagName,
    output: { currentTime: allTargetData.currentTime },
  })),
].forEach((expectation) => {
  test(`serializeEvent() ${expectation.case}`, () => {
    const eventData = {
      target: { ...allTargetData, tagName: expectation.tagName },
    };
    if (expectation.otherAttrs) {
      Object.assign(eventData.target, expectation.otherAttrs);
    }
    assert.equal(serializeEvent(eventData), expectation.output);
  });
});

const allEventData = {
  type: null, // set in text
  target: { tagName: null }, // avoid triggering target specific transformations
  clipboardData: "clipboardData",
  data: "data",
  altKey: "altKey",
  charCode: "charCode",
  ctrlKey: "ctrlKey",
  key: "key",
  keyCode: "keyCode",
  locale: "locale",
  location: "location",
  metaKey: "metaKey",
  repeat: "repeat",
  shiftKey: "shiftKey",
  which: "which",
  altKey: "altKey",
  button: "button",
  buttons: "buttons",
  clientX: "clientX",
  clientY: "clientY",
  ctrlKey: "ctrlKey",
  metaKey: "metaKey",
  pageX: "pageX",
  pageY: "pageY",
  screenX: "screenX",
  screenY: "screenY",
  shiftKey: "shiftKey",
  pointerId: "pointerId",
  width: "width",
  height: "height",
  pressure: "pressure",
  tiltX: "tiltX",
  tiltY: "tiltY",
  pointerType: "pointerType",
  isPrimary: "isPrimary",
  altKey: "altKey",
  ctrlKey: "ctrlKey",
  metaKey: "metaKey",
  shiftKey: "shiftKey",
  detail: "detail",
  deltaMode: "deltaMode",
  deltaX: "deltaX",
  deltaY: "deltaY",
  deltaZ: "deltaZ",
  animationName: "animationName",
  pseudoElement: "pseudoElement",
  elapsedTime: "elapsedTime",
  propertyName: "propertyName",
  pseudoElement: "pseudoElement",
  elapsedTime: "elapsedTime",
};

[
  ...["copy", "cut", "paste"].map((eventType) => ({
    eventType,
    case: "clipboard",
    output: { clipboardData: "clipboardData" },
  })),
  ...["compositionend", "compositionstart", "compositionupdate"].map(
    (eventType) => ({
      eventType,
      case: "composition",
      output: { data: "data" },
    })
  ),
  ...["keydown", "keypress", "keyup"].map((eventType) => ({
    eventType,
    case: "keyboard",
    output: {
      altKey: "altKey",
      charCode: "charCode",
      ctrlKey: "ctrlKey",
      key: "key",
      keyCode: "keyCode",
      locale: "locale",
      location: "location",
      metaKey: "metaKey",
      repeat: "repeat",
      shiftKey: "shiftKey",
      which: "which",
    },
  })),
  ...[
    "click",
    "contextmenu",
    "doubleclick",
    "drag",
    "dragend",
    "dragenter",
    "dragexit",
    "dragleave",
    "dragover",
    "dragstart",
    "drop",
    "mousedown",
    "mouseenter",
    "mouseleave",
    "mousemove",
    "mouseout",
    "mouseover",
    "mouseup",
  ].map((eventType) => ({
    eventType,
    case: "mouse",
    output: {
      altKey: "altKey",
      button: "button",
      buttons: "buttons",
      clientX: "clientX",
      clientY: "clientY",
      ctrlKey: "ctrlKey",
      metaKey: "metaKey",
      pageX: "pageX",
      pageY: "pageY",
      screenX: "screenX",
      screenY: "screenY",
      shiftKey: "shiftKey",
    },
  })),
  ...[
    "pointerdown",
    "pointermove",
    "pointerup",
    "pointercancel",
    "gotpointercapture",
    "lostpointercapture",
    "pointerenter",
    "pointerleave",
    "pointerover",
    "pointerout",
  ].map((eventType) => ({
    eventType,
    case: "pointer",
    output: {
      pointerId: "pointerId",
      width: "width",
      height: "height",
      pressure: "pressure",
      tiltX: "tiltX",
      tiltY: "tiltY",
      pointerType: "pointerType",
      isPrimary: "isPrimary",
    },
  })),
  ...["touchcancel", "touchend", "touchmove", "touchstart"].map(
    (eventType) => ({
      eventType,
      case: "touch",
      output: {
        altKey: "altKey",
        ctrlKey: "ctrlKey",
        metaKey: "metaKey",
        shiftKey: "shiftKey",
      },
    })
  ),
  {
    eventType: "scroll",
    case: "ui",
    output: {
      detail: "detail",
    },
  },
  {
    eventType: "wheel",
    case: "wheel",
    output: {
      deltaMode: "deltaMode",
      deltaX: "deltaX",
      deltaY: "deltaY",
      deltaZ: "deltaZ",
    },
  },
  ...["animationstart", "animationend", "animationiteration"].map(
    (eventType) => ({
      eventType,
      case: "animation",
      output: {
        animationName: "animationName",
        pseudoElement: "pseudoElement",
        elapsedTime: "elapsedTime",
      },
    })
  ),
  {
    eventType: "transitionend",
    case: "transition",
    output: {
      propertyName: "propertyName",
      pseudoElement: "pseudoElement",
      elapsedTime: "elapsedTime",
    },
  },
].forEach((expectation) => {
  test(`serializeEvent() adds ${expectation.case} attributes`, () => {
    assert.equal(
      serializeEvent({ ...allEventData, type: expectation.eventType }),
      expectation.output
    );
  });
});

const mockElementsToSelect = `
<div>
<p id="start"><span>START</span></p>
<p>MIDDLE</p>
<p id="end"><span>END</span></p>
</div>
`;

test("serializeEvent() adds text of current selection", () => {
  document.body.innerHTML = mockElementsToSelect;
  const start = document.getElementById("start");
  const end = document.getElementById("end");
  window.getSelection().setBaseAndExtent(start, 0, end, 0);
  assert.equal(serializeEvent({ ...allEventData, type: "select" }), {
    selectedText: "START\nMIDDLE\n",
  });
});

test.run();
