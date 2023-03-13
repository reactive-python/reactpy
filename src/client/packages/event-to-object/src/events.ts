// TODO
type FileListObject = any;
type DataTransferItemListObject = any;

export type EventToObjectMap = {
  event: [Event, EventObject];
  animation: [AnimationEvent, AnimationEventObject];
  clipboard: [ClipboardEvent, ClipboardEventObject];
  composition: [CompositionEvent, CompositionEventObject];
  devicemotion: [DeviceMotionEvent, DeviceMotionEventObject];
  deviceorientation: [DeviceOrientationEvent, DeviceOrientationEventObject];
  drag: [DragEvent, DragEventObject];
  focus: [FocusEvent, FocusEventObject];
  formdata: [FormDataEvent, FormDataEventObject];
  gamepad: [GamepadEvent, GamepadEventObject];
  input: [InputEvent, InputEventObject];
  keyboard: [KeyboardEvent, KeyboardEventObject];
  mouse: [MouseEvent, MouseEventObject];
  pointer: [PointerEvent, PointerEventObject];
  submit: [SubmitEvent, SubmitEventObject];
  touch: [TouchEvent, TouchEventObject];
  transition: [TransitionEvent, TransitionEventObject];
  ui: [UIEvent, UIEventObject];
  wheel: [WheelEvent, WheelEventObject];
};

export interface EventObject {
  bubbles: boolean;
  composed: boolean;
  currentTarget: ElementObject | null;
  defaultPrevented: boolean;
  eventPhase: number;
  isTrusted: boolean;
  target: ElementObject | null;
  timeStamp: DOMHighResTimeStamp;
  type: string;
  selection: SelectionObject | null;
}

export interface SubmitEventObject extends EventObject {
  submitter: ElementObject;
}

export interface InputEventObject extends UIEventObject {
  data: string | null;
  dataTransfer: DataTransferObject | null;
  isComposing: boolean;
  inputType: string;
}

export interface GamepadEventObject extends EventObject {
  gamepad: GamepadObject;
}

export interface GamepadObject {
  axes: number[];
  buttons: GamepadButtonObject[];
  connected: boolean;
  hapticActuators: GamepadHapticActuatorObject[];
  id: string;
  index: number;
  mapping: GamepadMappingType;
  timestamp: DOMHighResTimeStamp;
}

export interface GamepadButtonObject {
  pressed: boolean;
  touched: boolean;
  value: number;
}
export interface GamepadHapticActuatorObject {
  type: string;
}

export interface DragEventObject extends MouseEventObject {
  /** Returns the DataTransfer object for the event. */
  readonly dataTransfer: DataTransferObject | null;
}

export interface DeviceMotionEventObject extends EventObject {
  acceleration: DeviceAccelerationObject | null;
  accelerationIncludingGravity: DeviceAccelerationObject | null;
  interval: number;
  rotationRate: DeviceRotationRateObject | null;
}

export interface DeviceAccelerationObject {
  x: number | null;
  y: number | null;
  z: number | null;
}

export interface DeviceRotationRateObject {
  alpha: number | null;
  beta: number | null;
  gamma: number | null;
}

export interface DeviceOrientationEventObject extends EventObject {
  absolute: boolean;
  alpha: number | null;
  beta: number | null;
  gamma: number | null;
}

export interface MouseEventObject extends EventObject {
  altKey: boolean;
  button: number;
  buttons: number;
  clientX: number;
  clientY: number;
  ctrlKey: boolean;
  metaKey: boolean;
  movementX: number;
  movementY: number;
  offsetX: number;
  offsetY: number;
  pageX: number;
  pageY: number;
  relatedTarget: ElementObject | null;
  screenX: number;
  screenY: number;
  shiftKey: boolean;
  x: number;
  y: number;
}

export interface FormDataEventObject extends EventObject {
  formData: FormDataObject;
}

export type FormDataObject = [string, string | FileObject][];

export interface AnimationEventObject extends EventObject {
  animationName: string;
  elapsedTime: number;
  pseudoElement: string;
}

export interface ClipboardEventObject extends EventObject {
  clipboardData: DataTransferObject | null;
}

export interface UIEventObject extends EventObject {
  detail: number;
}

/** The DOM CompositionEvent represents events that occur due to the user indirectly
 * entering text. */
export interface CompositionEventObject extends UIEventObject {
  data: string;
}

export interface KeyboardEventObject extends UIEventObject {
  altKey: boolean;
  code: string;
  ctrlKey: boolean;
  isComposing: boolean;
  key: string;
  location: number;
  metaKey: boolean;
  repeat: boolean;
  shiftKey: boolean;
}

export interface FocusEventObject extends UIEventObject {
  relatedTarget: ElementObject | null;
}

export interface TouchEventObject extends UIEventObject {
  altKey: boolean;
  changedTouches: TouchObject[];
  ctrlKey: boolean;
  metaKey: boolean;
  shiftKey: boolean;
  targetTouches: TouchObject[];
  touches: TouchObject[];
}

export interface PointerEventObject extends MouseEventObject {
  height: number;
  isPrimary: boolean;
  pointerId: number;
  pointerType: string;
  pressure: number;
  tangentialPressure: number;
  tiltX: number;
  tiltY: number;
  twist: number;
  width: number;
}

export interface TransitionEventObject extends EventObject {
  elapsedTime: number;
  propertyName: string;
  pseudoElement: string;
}

export interface WheelEventObject extends MouseEventObject {
  readonly deltaMode: number;
  readonly deltaX: number;
  readonly deltaY: number;
  readonly deltaZ: number;
}

export interface TouchObject {
  clientX: number;
  clientY: number;
  force: number;
  identifier: number;
  pageX: number;
  pageY: number;
  radiusX: number;
  radiusY: number;
  rotationAngle: number;
  screenX: number;
  screenY: number;
  target: ElementObject;
}

export interface DataTransferObject {
  dropEffect: "none" | "copy" | "link" | "move";
  effectAllowed:
    | "none"
    | "copy"
    | "copyLink"
    | "copyMove"
    | "link"
    | "linkMove"
    | "move"
    | "all"
    | "uninitialized";
  files: FileListObject;
  items: DataTransferItemListObject;
  types: string[];
}

export interface SelectionObject {
  anchorNode: ElementObject | null;
  anchorOffset: number;
  focusNode: ElementObject | null;
  focusOffset: number;
  isCollapsed: boolean;
  rangeCount: number;
  type: string;
  selectedText: string;
}

export interface ElementObject {
  value?: string;
  textContent?: string;
}

export interface FileObject {
  name: string;
  size: number;
  type: string;
}

type NONE = 0;
type CAPTURING_PHASE = 1;
type AT_TARGET = 2;
type BUBBLING_PHASE = 3;
