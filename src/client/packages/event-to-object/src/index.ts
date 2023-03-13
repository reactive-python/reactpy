import * as e from "./events";

export default function convert<E extends Event>(
  event: E,
):
  | {
      [K in keyof e.EventToObjectMap]: e.EventToObjectMap[K] extends [
        E,
        infer P,
      ]
        ? P
        : never;
    }[keyof e.EventToObjectMap]
  | null {
  return event.type in eventConverters
    ? eventConverters[event.type](event)
    : convertEvent(event);
}

const convertEvent = (event: Event): e.EventObject => ({
  /** Returns true or false depending on how event was initialized. True if event goes
   * through its target's ancestors in reverse tree order, and false otherwise. */
  bubbles: event.bubbles,
  composed: event.composed,
  currentTarget: convertElement(event.currentTarget),
  defaultPrevented: event.defaultPrevented,
  eventPhase: event.eventPhase,
  isTrusted: event.isTrusted,
  target: convertElement(event.target),
  timeStamp: event.timeStamp,
  type: event.type,
  selection: convertSelection(window.getSelection()),
});

const convertClipboardEvent = (
  event: ClipboardEvent,
): e.ClipboardEventObject => ({
  ...convertEvent(event),
  clipboardData: convertDataTransferObject(event.clipboardData),
});

const convertCompositionEvent = (
  event: CompositionEvent,
): e.CompositionEventObject => ({
  ...convertUiEvent(event),
  data: event.data,
});

const convertInputEvent = (event: InputEvent): e.InputEventObject => ({
  ...convertUiEvent(event),
  data: event.data,
  inputType: event.inputType,
  dataTransfer: convertDataTransferObject(event.dataTransfer),
  isComposing: event.isComposing,
});

const convertKeyboardEvent = (event: KeyboardEvent): e.KeyboardEventObject => ({
  ...convertUiEvent(event),
  code: event.code,
  isComposing: event.isComposing,
  altKey: event.altKey,
  ctrlKey: event.ctrlKey,
  key: event.key,
  location: event.location,
  metaKey: event.metaKey,
  repeat: event.repeat,
  shiftKey: event.shiftKey,
});

const convertMouseEvent = (event: MouseEvent): e.MouseEventObject => ({
  ...convertEvent(event),
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
  movementX: event.movementX,
  movementY: event.movementY,
  offsetX: event.offsetX,
  offsetY: event.offsetY,
  x: event.x,
  y: event.y,
  relatedTarget: convertElement(event.relatedTarget),
});

const convertTouchEvent = (event: TouchEvent): e.TouchEventObject => ({
  ...convertUiEvent(event),
  altKey: event.altKey,
  ctrlKey: event.ctrlKey,
  metaKey: event.metaKey,
  shiftKey: event.shiftKey,
  touches: Array.from(event.touches).map(convertTouch),
  changedTouches: Array.from(event.changedTouches).map(convertTouch),
  targetTouches: Array.from(event.targetTouches).map(convertTouch),
});

const convertUiEvent = (event: UIEvent): e.UIEventObject => ({
  ...convertEvent(event),
  detail: event.detail,
});

const convertAnimationEvent = (
  event: AnimationEvent,
): e.AnimationEventObject => ({
  ...convertEvent(event),
  animationName: event.animationName,
  pseudoElement: event.pseudoElement,
  elapsedTime: event.elapsedTime,
});

const convertTransitionEvent = (
  event: TransitionEvent,
): e.TransitionEventObject => ({
  ...convertEvent(event),
  propertyName: event.propertyName,
  pseudoElement: event.pseudoElement,
  elapsedTime: event.elapsedTime,
});

const convertFocusEvent = (event: FocusEvent): e.FocusEventObject => ({
  ...convertUiEvent(event),
  relatedTarget: convertElement(event.relatedTarget),
});

const convertDeviceOrientationEvent = (
  event: DeviceOrientationEvent,
): e.DeviceOrientationEventObject => ({
  ...convertEvent(event),
  absolute: event.absolute,
  alpha: event.alpha,
  beta: event.beta,
  gamma: event.gamma,
});

const convertDragEvent = (event: DragEvent): e.DragEventObject => ({
  ...convertMouseEvent(event),
  dataTransfer: convertDataTransferObject(event.dataTransfer),
});

const convertGamepadEvent = (event: GamepadEvent): e.GamepadEventObject => ({
  ...convertEvent(event),
  gamepad: convertGamepad(event.gamepad),
});

const convertPointerEvent = (event: PointerEvent): e.PointerEventObject => ({
  ...convertMouseEvent(event),
  pointerId: event.pointerId,
  width: event.width,
  height: event.height,
  pressure: event.pressure,
  tiltX: event.tiltX,
  tiltY: event.tiltY,
  pointerType: event.pointerType,
  isPrimary: event.isPrimary,
  tangentialPressure: event.tangentialPressure,
  twist: event.twist,
});

const convertWheelEvent = (event: WheelEvent): e.WheelEventObject => ({
  ...convertMouseEvent(event),
  deltaMode: event.deltaMode,
  deltaX: event.deltaX,
  deltaY: event.deltaY,
  deltaZ: event.deltaZ,
});

const convertSubmitEvent = (event: SubmitEvent): e.SubmitEventObject => ({
  ...convertEvent(event),
  submitter: convertElement(event.submitter),
});

const eventConverters: { [key: string]: (event: any) => any } = {
  // animation events
  animationcancel: convertAnimationEvent,
  animationend: convertAnimationEvent,
  animationiteration: convertAnimationEvent,
  animationstart: convertAnimationEvent,
  // input events
  beforeinput: convertInputEvent,
  // composition events
  compositionend: convertCompositionEvent,
  compositionstart: convertCompositionEvent,
  compositionupdate: convertCompositionEvent,
  // clipboard events
  copy: convertClipboardEvent,
  cut: convertClipboardEvent,
  paste: convertClipboardEvent,
  // device orientation events
  deviceorientation: convertDeviceOrientationEvent,
  // drag events
  drag: convertDragEvent,
  dragend: convertDragEvent,
  dragenter: convertDragEvent,
  dragleave: convertDragEvent,
  dragover: convertDragEvent,
  dragstart: convertDragEvent,
  drop: convertDragEvent,
  // ui events
  error: convertUiEvent,
  // focus events
  blur: convertFocusEvent,
  focus: convertFocusEvent,
  focusin: convertFocusEvent,
  focusout: convertFocusEvent,
  // gamepad events
  gamepadconnected: convertGamepadEvent,
  gamepaddisconnected: convertGamepadEvent,
  // keyboard events
  keydown: convertKeyboardEvent,
  keypress: convertKeyboardEvent,
  keyup: convertKeyboardEvent,
  // mouse events
  auxclick: convertMouseEvent,
  click: convertMouseEvent,
  dblclick: convertMouseEvent,
  contextmenu: convertMouseEvent,
  mousedown: convertMouseEvent,
  mouseenter: convertMouseEvent,
  mouseleave: convertMouseEvent,
  mousemove: convertMouseEvent,
  mouseout: convertMouseEvent,
  mouseover: convertMouseEvent,
  mouseup: convertMouseEvent,
  scroll: convertMouseEvent,
  // pointer events
  gotpointercapture: convertPointerEvent,
  lostpointercapture: convertPointerEvent,
  pointercancel: convertPointerEvent,
  pointerdown: convertPointerEvent,
  pointerenter: convertPointerEvent,
  pointerleave: convertPointerEvent,
  pointerlockchange: convertPointerEvent,
  pointerlockerror: convertPointerEvent,
  pointermove: convertPointerEvent,
  pointerout: convertPointerEvent,
  pointerover: convertPointerEvent,
  pointerup: convertPointerEvent,
  // submit events
  submit: convertSubmitEvent,
  // touch events
  touchcancel: convertTouchEvent,
  touchend: convertTouchEvent,
  touchmove: convertTouchEvent,
  touchstart: convertTouchEvent,
  // transition events
  transitioncancel: convertTransitionEvent,
  transitionend: convertTransitionEvent,
  transitionrun: convertTransitionEvent,
  transitionstart: convertTransitionEvent,
  // wheel events
  wheel: convertWheelEvent,
};

function convertElement(element: EventTarget | HTMLElement | null): any {
  if (!element || !("tagName" in element)) {
    return null;
  }

  const htmlElement = element as HTMLElement;

  return {
    ...convertGenericElement(htmlElement),
    ...(htmlElement.tagName in elementConverters
      ? elementConverters[htmlElement.tagName](htmlElement)
      : {}),
  };
}

const convertGenericElement = (element: HTMLElement) => ({
  tagName: element.tagName,
  boundingClientRect: { ...element.getBoundingClientRect() },
});

const convertMediaElement = (element: HTMLMediaElement) => ({
  currentTime: element.currentTime,
  duration: element.duration,
  ended: element.ended,
  error: element.error,
  seeking: element.seeking,
  volume: element.volume,
});

const elementConverters: { [key: string]: (element: any) => any } = {
  AUDIO: convertMediaElement,
  BUTTON: (element: HTMLButtonElement) => ({ value: element.value }),
  DATA: (element: HTMLDataElement) => ({ value: element.value }),
  DATALIST: (element: HTMLDataListElement) => ({
    options: Array.from(element.options).map(elementConverters["OPTION"]),
  }),
  DIALOG: (element: HTMLDialogElement) => ({
    returnValue: element.returnValue,
  }),
  FIELDSET: (element: HTMLFieldSetElement) => ({
    elements: Array.from(element.elements).map(convertElement),
  }),
  FORM: (element: HTMLFormElement) => ({
    elements: Array.from(element.elements).map(convertElement),
  }),
  INPUT: (element: HTMLInputElement) => ({ value: element.value }),
  METER: (element: HTMLMeterElement) => ({ value: element.value }),
  OPTION: (element: HTMLOptionElement) => ({ value: element.value }),
  OUTPUT: (element: HTMLOutputElement) => ({ value: element.value }),
  PROGRESS: (element: HTMLProgressElement) => ({ value: element.value }),
  SELECT: (element: HTMLSelectElement) => ({ value: element.value }),
  TEXTAREA: (element: HTMLTextAreaElement) => ({ value: element.value }),
  VIDEO: convertMediaElement,
};

const convertGamepad = (gamepad: Gamepad): e.GamepadObject => ({
  axes: Array.from(gamepad.axes),
  buttons: Array.from(gamepad.buttons).map(convertGamepadButton),
  connected: gamepad.connected,
  id: gamepad.id,
  index: gamepad.index,
  mapping: gamepad.mapping,
  timestamp: gamepad.timestamp,
  hapticActuators: Array.from(gamepad.hapticActuators).map(
    convertGamepadHapticActuator,
  ),
});

const convertGamepadButton = (
  button: GamepadButton,
): e.GamepadButtonObject => ({
  pressed: button.pressed,
  touched: button.touched,
  value: button.value,
});

const convertGamepadHapticActuator = (
  actuator: GamepadHapticActuator,
): e.GamepadHapticActuatorObject => ({
  type: actuator.type,
});

const convertFile = (file: File) => ({
  lastModified: file.lastModified,
  name: file.name,
  size: file.size,
  type: file.type,
});

function convertDataTransferObject(
  dataTransfer: DataTransfer | null,
): e.DataTransferObject | null {
  if (!dataTransfer) {
    return null;
  }
  const { dropEffect, effectAllowed, files, items, types } = dataTransfer;
  return {
    dropEffect,
    effectAllowed,
    files: Array.from(files).map(convertFile),
    items: Array.from(items).map((item) => ({
      kind: item.kind,
      type: item.type,
    })),
    types: Array.from(types),
  };
}

function convertSelection(
  selection: Selection | null,
): e.SelectionObject | null {
  if (!selection) {
    return null;
  }
  const {
    type,
    anchorNode,
    anchorOffset,
    focusNode,
    focusOffset,
    isCollapsed,
    rangeCount,
  } = selection;
  if (type === "None") {
    return null;
  }
  return {
    type,
    anchorNode: convertElement(anchorNode),
    anchorOffset,
    focusNode: convertElement(focusNode),
    focusOffset,
    isCollapsed,
    rangeCount,
    selectedText: selection.toString(),
  };
}

function convertTouch({
  identifier,
  pageX,
  pageY,
  screenX,
  screenY,
  clientX,
  clientY,
  force,
  radiusX,
  radiusY,
  rotationAngle,
  target,
}: Touch): e.TouchObject {
  return {
    identifier,
    pageX,
    pageY,
    screenX,
    screenY,
    clientX,
    clientY,
    force,
    radiusX,
    radiusY,
    rotationAngle,
    target: convertElement(target),
  };
}
