import * as assert from "uvu/assert";
import { Event } from "happy-dom";
// @ts-ignore
import lodash from "lodash";
import convert from "../../src/index";
import { mockElementObject } from "./mock";

export function checkEventConversion(
  givenEvent: Event,
  expectedConversion: any,
): void {
  const actualSerializedEvent = convert(
    // @ts-ignore
    givenEvent,
  );

  if (!actualSerializedEvent) {
    assert.equal(actualSerializedEvent, expectedConversion);
    return;
  }

  // too hard to compare
  assert.equal(typeof actualSerializedEvent.timeStamp, "number");

  assert.equal(
    actualSerializedEvent,
    lodash.merge(
      { timeStamp: actualSerializedEvent.timeStamp, type: givenEvent.type },
      expectedConversionDefaults,
      expectedConversion,
    ),
  );

  // verify result is JSON serializable
  JSON.stringify(actualSerializedEvent);
}

const expectedConversionDefaults = {
  target: null,
  currentTarget: null,
  bubbles: false,
  composed: false,
  defaultPrevented: false,
  eventPhase: undefined,
  isTrusted: undefined,
  selection: null,
};
