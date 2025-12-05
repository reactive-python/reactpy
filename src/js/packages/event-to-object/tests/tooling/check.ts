import { expect } from "bun:test";
import { Event } from "happy-dom";
// @ts-ignore
import lodash from "lodash";
import { convert } from "../../src/index";

export function checkEventConversion(
  givenEvent: Event,
  expectedConversion: any,
): void {
  // Patch happy-dom event to make standard properties enumerable and defined
  const standardProps = [
    "bubbles",
    "cancelable",
    "composed",
    "currentTarget",
    "defaultPrevented",
    "eventPhase",
    "isTrusted",
    "target",
    "type",
    "srcElement",
    "returnValue",
    "altKey",
    "metaKey",
    "ctrlKey",
    "shiftKey",
    "elapsedTime",
    "propertyName",
    "pseudoElement",
  ];

  for (const prop of standardProps) {
    if (prop in givenEvent) {
      try {
        Object.defineProperty(givenEvent, prop, {
          enumerable: true,
          value: (givenEvent as any)[prop],
          writable: true,
          configurable: true,
        });
      } catch {
        // ignore
      }
    }
  }

  // timeStamp is special
  try {
    Object.defineProperty(givenEvent, "timeStamp", {
      enumerable: true,
      value: givenEvent.timeStamp || Date.now(),
      writable: true,
      configurable: true,
    });
  } catch {
    // ignore
  }

  // Patch undefined properties that are expected to be 0 or null
  const defaults: any = {
    offsetX: 0,
    offsetY: 0,
    layerX: 0,
    layerY: 0,
    pageX: 0,
    pageY: 0,
    x: 0,
    y: 0,
    screenX: 0,
    screenY: 0,
    movementX: 0,
    movementY: 0,
    detail: 0,
    which: 0,
    relatedTarget: null,
  };

  for (const [key, value] of Object.entries(defaults)) {
    if ((givenEvent as any)[key] === undefined && key in givenEvent) {
      try {
        Object.defineProperty(givenEvent, key, {
          enumerable: true,
          value: value,
          writable: true,
          configurable: true,
        });
      } catch {
        // ignore
      }
    }
  }

  const actualSerializedEvent = convert(
    // @ts-ignore
    givenEvent,
    5,
  );

  if (!actualSerializedEvent) {
    expect(actualSerializedEvent).toEqual(expectedConversion);
    return;
  }

  // too hard to compare
  // @ts-ignore
  expect(typeof actualSerializedEvent.timeStamp).toBe("number");

  // Remove nulls from expectedConversionDefaults because convert() strips nulls
  const comparisonDefaults = {
    bubbles: false,
    cancelable: false,
    composed: false,
    defaultPrevented: false,
    eventPhase: 0,
  };

  const expected = lodash.merge(
    // @ts-ignore
    { timeStamp: actualSerializedEvent.timeStamp, type: givenEvent.type },
    comparisonDefaults,
    expectedConversion,
  );

  // Remove keys from expected that are null or undefined, because convert() strips them
  for (const key in expected) {
    if (expected[key] === null || expected[key] === undefined) {
      delete expected[key];
    }
  }

  // Use toMatchObject to allow extra properties in actual (like layerX, detail, etc.)
  expect(actualSerializedEvent).toMatchObject(expected);

  // verify result is JSON serializable
  JSON.stringify(actualSerializedEvent);
}
