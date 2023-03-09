// @ts-ignore
import { window } from "./tooling/setup";
import { test } from "uvu";
import { checkEventConversion } from "./tooling/check";
import { mockElement } from "./tooling/mock";

type SimpleTestCase = {
  types: string[];
  description: string;
  givenEventType: new (type: string) => Event;
  expectedConversion: any;
};

const simpleTestCases: SimpleTestCase[] = [
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
    types: ["copy", "cut", "paste"],
    description: "clipboad event",
    givenEventType: window.ClipboardEvent,
    expectedConversion: { clipboardData: null },
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
];

simpleTestCases.forEach((testCase) => {
  testCase.types.forEach((type) => {
    test(`converts ${type} ${testCase.description}`, () => {
      const event = new testCase.givenEventType(type);
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
  checkEventConversion(new Event("fake"), {
    type: "fake",
    selection: {
      type: "Range",
      anchorNode: { ...mockElement, tagName: "P" },
      anchorOffset: 0,
      focusNode: { ...mockElement, tagName: "P" },
      focusOffset: 0,
      isCollapsed: false,
      rangeCount: 1,
      selectedText: "START\n  MIDDLE\n  ",
    },
    eventPhase: 0,
    isTrusted: false,
  });
});

test.run();
