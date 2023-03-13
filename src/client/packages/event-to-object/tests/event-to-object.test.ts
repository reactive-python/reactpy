// @ts-ignore
import { window } from "./tooling/setup";
import { test } from "uvu";
import { Event } from "happy-dom";
import { checkEventConversion } from "./tooling/check";
import {
  mockElementObject,
  mockGamepad,
  mockTouch,
  mockTouchObject,
} from "./tooling/mock";

type SimpleTestCase<E extends Event> = {
  types: string[];
  description: string;
  givenEventType: new (type: string) => E;
  expectedConversion: any;
  initGivenEvent?: (event: E) => void;
};

const simpleTestCases: SimpleTestCase<any>[] = [
  {
    types: [
      "animationcancel",
      "animationend",
      "animationiteration",
      "animationstart",
    ],
    description: "animation event",
    givenEventType: window.AnimationEvent,
    expectedConversion: {
      animationName: "",
      pseudoElement: "",
      elapsedTime: 0,
    },
  },
  {
    types: ["beforeinput"],
    description: "event",
    givenEventType: window.InputEvent,
    expectedConversion: {
      detail: 0,
      data: "",
      inputType: "",
      dataTransfer: null,
      isComposing: false,
    },
  },
  {
    types: ["compositionend", "compositionstart", "compositionupdate"],
    description: "composition event",
    givenEventType: window.CompositionEvent,
    expectedConversion: {
      data: undefined,
      detail: undefined,
    },
  },
  {
    types: ["copy", "cut", "paste"],
    description: "clipboad event",
    givenEventType: window.ClipboardEvent,
    expectedConversion: { clipboardData: null },
  },
  {
    types: [
      "drag",
      "dragend",
      "dragenter",
      "dragleave",
      "dragover",
      "dragstart",
      "drop",
    ],
    description: "drag event",
    givenEventType: window.DragEvent,
    expectedConversion: {
      altKey: undefined,
      button: undefined,
      buttons: undefined,
      clientX: undefined,
      clientY: undefined,
      ctrlKey: undefined,
      dataTransfer: null,
      metaKey: undefined,
      movementX: undefined,
      movementY: undefined,
      offsetX: undefined,
      offsetY: undefined,
      pageX: undefined,
      pageY: undefined,
      relatedTarget: null,
      screenX: undefined,
      screenY: undefined,
      shiftKey: undefined,
      x: undefined,
      y: undefined,
    },
  },
  {
    types: ["error"],
    description: "event",
    givenEventType: window.ErrorEvent,
    expectedConversion: { detail: 0 },
  },
  {
    types: ["blur", "focus", "focusin", "focusout"],
    description: "focus event",
    givenEventType: window.FocusEvent,
    expectedConversion: {
      relatedTarget: null,
      detail: 0,
    },
  },
  {
    types: ["gamepadconnected", "gamepaddisconnected"],
    description: "gamepad event",
    givenEventType: window.GamepadEvent,
    expectedConversion: { gamepad: mockGamepad },
    initGivenEvent: (event) => {
      event.gamepad = mockGamepad;
    },
  },
  {
    types: ["keydown", "keypress", "keyup"],
    description: "keyboard event",
    givenEventType: window.KeyboardEvent,
    expectedConversion: {
      altKey: false,
      code: "",
      ctrlKey: false,
      isComposing: false,
      key: "",
      location: 0,
      metaKey: false,
      repeat: false,
      shiftKey: false,
      detail: 0,
    },
  },
  {
    types: [
      "click",
      "auxclick",
      "dblclick",
      "mousedown",
      "mouseenter",
      "mouseleave",
      "mousemove",
      "mouseout",
      "mouseover",
      "mouseup",
      "scroll",
    ],
    description: "mouse event",
    givenEventType: window.MouseEvent,
    expectedConversion: {
      altKey: false,
      button: 0,
      buttons: 0,
      clientX: 0,
      clientY: 0,
      ctrlKey: false,
      metaKey: false,
      movementX: 0,
      movementY: 0,
      offsetX: 0,
      offsetY: 0,
      pageX: 0,
      pageY: 0,
      relatedTarget: null,
      screenX: 0,
      screenY: 0,
      shiftKey: false,
      x: undefined,
      y: undefined,
    },
  },
  {
    types: [
      "auxclick",
      "click",
      "contextmenu",
      "dblclick",
      "mousedown",
      "mouseenter",
      "mouseleave",
      "mousemove",
      "mouseout",
      "mouseover",
      "mouseup",
    ],
    description: "mouse event",
    givenEventType: window.MouseEvent,
    expectedConversion: {
      altKey: false,
      button: 0,
      buttons: 0,
      clientX: 0,
      clientY: 0,
      ctrlKey: false,
      metaKey: false,
      movementX: 0,
      movementY: 0,
      offsetX: 0,
      offsetY: 0,
      pageX: 0,
      pageY: 0,
      relatedTarget: null,
      screenX: 0,
      screenY: 0,
      shiftKey: false,
      x: undefined,
      y: undefined,
    },
  },
  {
    types: [
      "gotpointercapture",
      "lostpointercapture",
      "pointercancel",
      "pointerdown",
      "pointerenter",
      "pointerleave",
      "pointerlockchange",
      "pointerlockerror",
      "pointermove",
      "pointerout",
      "pointerover",
      "pointerup",
    ],
    description: "pointer event",
    givenEventType: window.PointerEvent,
    expectedConversion: {
      altKey: false,
      button: 0,
      buttons: 0,
      clientX: 0,
      clientY: 0,
      ctrlKey: false,
      metaKey: false,
      movementX: 0,
      movementY: 0,
      offsetX: 0,
      offsetY: 0,
      pageX: 0,
      pageY: 0,
      relatedTarget: null,
      screenX: 0,
      screenY: 0,
      shiftKey: false,
      x: undefined,
      y: undefined,
      pointerId: 0,
      pointerType: "",
      pressure: 0,
      tiltX: 0,
      tiltY: 0,
      width: 0,
      height: 0,
      isPrimary: false,
      twist: 0,
      tangentialPressure: 0,
    },
  },
  {
    types: ["submit"],
    description: "event",
    givenEventType: window.Event,
    expectedConversion: { submitter: null },
    initGivenEvent: (event) => {
      event.submitter = null;
    },
  },
  {
    types: ["touchcancel", "touchend", "touchmove", "touchstart"],
    description: "touch event",
    givenEventType: window.TouchEvent,
    expectedConversion: {
      altKey: undefined,
      changedTouches: [mockTouchObject],
      ctrlKey: undefined,
      metaKey: undefined,
      targetTouches: [mockTouchObject],
      touches: [mockTouchObject],
      detail: undefined,
      shiftKey: undefined,
    },
    initGivenEvent: (event) => {
      event.changedTouches = [mockTouch];
      event.targetTouches = [mockTouch];
      event.touches = [mockTouch];
    },
  },
  {
    types: [
      "transitioncancel",
      "transitionend",
      "transitionrun",
      "transitionstart",
    ],
    description: "transition event",
    givenEventType: window.TransitionEvent,
    expectedConversion: {
      propertyName: undefined,
      elapsedTime: undefined,
      pseudoElement: undefined,
    },
  },
  {
    types: ["wheel"],
    description: "wheel event",
    givenEventType: window.WheelEvent,
    expectedConversion: {
      altKey: undefined,
      button: undefined,
      buttons: undefined,
      clientX: undefined,
      clientY: undefined,
      ctrlKey: undefined,
      deltaMode: 0,
      deltaX: 0,
      deltaY: 0,
      deltaZ: 0,
      metaKey: undefined,
      movementX: undefined,
      movementY: undefined,
      offsetX: undefined,
      offsetY: undefined,
      pageX: 0,
      pageY: 0,
      relatedTarget: null,
      screenX: undefined,
      screenY: undefined,
      shiftKey: undefined,
      x: undefined,
      y: undefined,
    },
  },
];

simpleTestCases.forEach((testCase) => {
  testCase.types.forEach((type) => {
    test(`converts ${type} ${testCase.description}`, () => {
      const event = new testCase.givenEventType(type);
      if (testCase.initGivenEvent) {
        testCase.initGivenEvent(event);
      }
      checkEventConversion(event, testCase.expectedConversion);
    });
  });
});

test("adds text of current selection", () => {
  document.body.innerHTML = `
  <div>
  <p id="start"><span>START</span></p>
  <p>MIDDLE</p>
  <p id="end"><span>END</span></p>
  </div>
  `;
  const start = document.getElementById("start");
  const end = document.getElementById("end");
  window.getSelection()!.setBaseAndExtent(start!, 0, end!, 0);
  checkEventConversion(new window.Event("fake"), {
    type: "fake",
    selection: {
      type: "Range",
      anchorNode: { ...mockElementObject, tagName: "P" },
      anchorOffset: 0,
      focusNode: { ...mockElementObject, tagName: "P" },
      focusOffset: 0,
      isCollapsed: false,
      rangeCount: 1,
      selectedText: "START\n  MIDDLE\n  ",
    },
    eventPhase: undefined,
    isTrusted: undefined,
  });
});

test.run();
