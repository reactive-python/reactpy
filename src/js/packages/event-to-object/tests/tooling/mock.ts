export const mockBoundingRect = {
  left: 0,
  top: 0,
  right: 0,
  bottom: 0,
  x: 0,
  y: 0,
  height: 0,
  width: 0,
};

export const mockElementObject = {
  tagName: null,
  boundingClientRect: mockBoundingRect,
};

export const mockElement = {
  tagName: null,
  getBoundingClientRect: () => mockBoundingRect,
};

export const mockGamepad = {
  id: "test",
  index: 0,
  connected: true,
  mapping: "standard",
  axes: [],
  buttons: [
    {
      pressed: false,
      touched: false,
      value: 0,
    },
  ],
  hapticActuators: [
    {
      type: "vibration",
    },
  ],
  timestamp: undefined,
};

export const mockTouch = {
  identifier: 0,
  pageX: 0,
  pageY: 0,
  screenX: 0,
  screenY: 0,
  clientX: 0,
  clientY: 0,
  force: 0,
  radiusX: 0,
  radiusY: 0,
  rotationAngle: 0,
  target: mockElement,
};

export const mockTouchObject = {
  ...mockTouch,
  target: mockElementObject,
};
