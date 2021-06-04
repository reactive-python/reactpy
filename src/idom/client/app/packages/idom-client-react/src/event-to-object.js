function serializeEvent(event) {
  const data = {};

  if (event.type in eventTransforms) {
    Object.assign(data, eventTransforms[event.type](event));
  }

  const target = event.target;
  if (target.tagName in targetTransforms) {
    targetTransforms[target.tagName].forEach((trans) =>
      Object.assign(data, trans(target))
    );
  }

  return data;
}

const targetTransformCategories = {
  hasValue: (target) => ({
    value: target.value,
  }),
  hasCurrentTime: (target) => ({
    currentTime: target.currentTime,
  }),
  hasFiles: (target) => {
    if (target?.type == "file") {
      return {
        files: Array.from(target.files).map((file) => ({
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

const targetTagCategories = {
  hasValue: ["BUTTON", "INPUT", "OPTION", "LI", "METER", "PROGRESS", "PARAM"],
  hasCurrentTime: ["AUDIO", "VIDEO"],
  hasFiles: ["INPUT"],
};

const targetTransforms = {};

Object.keys(targetTagCategories).forEach((category) => {
  targetTagCategories[category].forEach((type) => {
    const transforms = targetTransforms[type] || (targetTransforms[type] = []);
    transforms.push(targetTransformCategories[category]);
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

export default serializeEvent;
