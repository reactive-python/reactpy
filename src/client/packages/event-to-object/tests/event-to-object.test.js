import { test } from "uvu";
import lodash from "lodash";
import * as assert from "uvu/assert";
import serializeEvent from "../src/index.ts";
import "./tooling/setup.js";

const mockBoundingRect = {
  left: 0,
  top: 0,
  right: 0,
  bottom: 0,
  x: 0,
  y: 0,
  width: 0,
};

const mockElement = {
  tagName: null,
  getBoundingClientRect: () => mockBoundingRect,
};

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
  elements: [
    { ...mockElement, tagName: "INPUT", value: "first" },
    { ...mockElement, tagName: "INPUT", value: "second" },
  ],
};

function assertEqualSerializedEventData(eventData, expectedSerializedData) {
  const commonEventData = {
    target: mockElement,
    currentTarget: mockElement,
    relatedTarget: mockElement,
  };

  const commonSerializedEventData = {
    target: { boundingClientRect: mockBoundingRect },
    currentTarget: { boundingClientRect: mockBoundingRect },
    relatedTarget: { boundingClientRect: mockBoundingRect },
  };

  assert.equal(
    serializeEvent(lodash.merge({}, commonEventData, eventData)),
    lodash.merge({}, commonSerializedEventData, expectedSerializedData),
  );
}

[
  {
    case: "adds 'files' and 'value' attributes for INPUT if type=file",
    tagName: "INPUT",
    addTargetAttrs: { type: "file" },
    output: {
      target: {
        files: allTargetData.files,
        value: allTargetData.value,
      },
    },
  },
  ...["BUTTON", "INPUT", "OPTION", "LI", "METER", "PROGRESS", "PARAM"].map(
    (tagName) => ({
      case: `adds 'value' attribute for ${tagName} element`,
      tagName,
      output: { target: { value: allTargetData.value } },
    }),
  ),
  ...["AUDIO", "VIDEO"].map((tagName) => ({
    case: `adds 'currentTime' attribute for ${tagName} element`,
    tagName,
    output: { target: { currentTime: allTargetData.currentTime } },
  })),
  ...["FORM"].map((tagName) => ({
    case: `adds 'elements' attribute for ${tagName} element`,
    tagName,
    output: {
      target: {
        elements: [
          {
            value: "first",
            boundingClientRect: mockBoundingRect,
          },
          {
            value: "second",
            boundingClientRect: mockBoundingRect,
          },
        ],
      },
    },
  })),
].forEach((expectation) => {
  test(`serializeEvent() ${expectation.case}`, () => {
    const eventData = {
      target: {
        ...allTargetData,
        tagName: expectation.tagName,
      },
    };
    if (expectation.addTargetAttrs) {
      Object.assign(eventData.target, expectation.addTargetAttrs);
    }
    assertEqualSerializedEventData(eventData, expectation.output);
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
  form: "form",
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
    }),
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
    }),
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
    }),
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
    assertEqualSerializedEventData(
      { ...allEventData, type: expectation.eventType },
      expectation.output,
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
  assertEqualSerializedEventData(
    { ...allEventData, type: "select" },
    {
      selectedText: "START\nMIDDLE\n",
    },
  );
});

test.run();
