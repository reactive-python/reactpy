export function serializeEvent(event) {
  const data = {};

  if (event.type in eventTransforms) {
    Object.assign(data, eventTransforms[event.type](event));
  }

  data.target = serializeDomElement(event.target);
  data.currentTarget =
    event.target === event.currentTarget
      ? data.target
      : serializeDomElement(event.currentTarget);
  data.relatedTarget = serializeDomElement(event.relatedTarget);

  return data;
}

function serializeDomElement(element) {
  let elementData = null;
  if (element) {
    elementData = defaultElementTransform(element);
    if (element.tagName in elementTransforms) {
      elementTransforms[element.tagName].forEach((trans) =>
        Object.assign(elementData, trans(element))
      );
    }
  }
  return elementData;
}

const elementTransformCategories = {
  hasValue: (element) => ({
    value: element.value,
  }),
  hasCurrentTime: (element) => ({
    currentTime: element.currentTime,
  }),
  hasFiles: (element) => {
    if (element?.type === "file") {
      return {
        files: Array.from(element.files).map((file) => ({
          lastModified: file.lastModified,
          name: file.name,
          size: file.size,
          type: file.type,
        })),
      };
    } else {
      return {};
    }
  },
};

function defaultElementTransform(element) {
  return { boundingClientRect: element.getBoundingClientRect() };
}

const elementTagCategories = {
  hasValue: [
    "BUTTON",
    "INPUT",
    "OPTION",
    "LI",
    "METER",
    "PROGRESS",
    "PARAM",
    "SELECT",
    "TEXTAREA",
  ],
  hasCurrentTime: ["AUDIO", "VIDEO"],
  hasFiles: ["INPUT"],
};

const elementTransforms = {};

Object.keys(elementTagCategories).forEach((category) => {
  elementTagCategories[category].forEach((type) => {
    const transforms =
      elementTransforms[type] || (elementTransforms[type] = []);
    transforms.push(elementTransformCategories[category]);
  });
});

const eventTransformCategories = {
  clipboard: (event) => ({
    clipboardData: event.clipboardData,
  }),
  composition: (event) => ({
    data: event.data,
  }),
  keyboard: (event) => ({
    altKey: event.altKey,
    charCode: event.charCode,
    ctrlKey: event.ctrlKey,
    key: event.key,
    keyCode: event.keyCode,
    locale: event.locale,
    location: event.location,
    metaKey: event.metaKey,
    repeat: event.repeat,
    shiftKey: event.shiftKey,
    which: event.which,
  }),
  mouse: (event) => ({
    altKey: event.altKey,
    button: event.button,
    buttons: event.buttons,
    clientX: event.clientX,
    clientY: event.clientY,
    ctrlKey: event.ctrlKey,
    metaKey: event.metaKey,
    pageX: event.pageX,
    pageY: event.pageY,
    screenX: event.screenX,
    screenY: event.screenY,
    shiftKey: event.shiftKey,
  }),
  pointer: (event) => ({
    pointerId: event.pointerId,
    width: event.width,
    height: event.height,
    pressure: event.pressure,
    tiltX: event.tiltX,
    tiltY: event.tiltY,
    pointerType: event.pointerType,
    isPrimary: event.isPrimary,
  }),
  selection: () => {
    return { selectedText: window.getSelection().toString() };
  },
  touch: (event) => ({
    altKey: event.altKey,
    ctrlKey: event.ctrlKey,
    metaKey: event.metaKey,
    shiftKey: event.shiftKey,
  }),
  ui: (event) => ({
    detail: event.detail,
  }),
  wheel: (event) => ({
    deltaMode: event.deltaMode,
    deltaX: event.deltaX,
    deltaY: event.deltaY,
    deltaZ: event.deltaZ,
  }),
  animation: (event) => ({
    animationName: event.animationName,
    pseudoElement: event.pseudoElement,
    elapsedTime: event.elapsedTime,
  }),
  transition: (event) => ({
    propertyName: event.propertyName,
    pseudoElement: event.pseudoElement,
    elapsedTime: event.elapsedTime,
  }),
};

const eventTypeCategories = {
  clipboard: ["copy", "cut", "paste"],
  composition: ["compositionend", "compositionstart", "compositionupdate"],
  keyboard: ["keydown", "keypress", "keyup"],
  mouse: [
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
  ],
  pointer: [
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
  ],
  selection: ["select"],
  touch: ["touchcancel", "touchend", "touchmove", "touchstart"],
  ui: ["scroll"],
  wheel: ["wheel"],
  animation: ["animationstart", "animationend", "animationiteration"],
  transition: ["transitionend"],
};

const eventTransforms = {};

Object.keys(eventTypeCategories).forEach((category) => {
  eventTypeCategories[category].forEach((type) => {
    eventTransforms[type] = eventTransformCategories[category];
  });
});
