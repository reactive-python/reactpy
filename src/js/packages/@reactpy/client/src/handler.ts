// Shared marker property names attached to event handler functions created by
// `vdom.tsx::createEventHandler`. Centralizing these strings keeps `components.tsx`
// and `vdom.tsx` in sync without relying on ad-hoc property names.

export const HANDLER_MARKER = "isHandler" as const;
export const HANDLER_DEBOUNCE = "debounce" as const;
export const HANDLER_THROTTLE = "throttle" as const;

export type HandlerMarker = typeof HANDLER_MARKER;
export type HandlerDebounce = typeof HANDLER_DEBOUNCE;
export type HandlerThrottle = typeof HANDLER_THROTTLE;

export type TaggedEventHandler = ((event: Event) => void) & {
  [HANDLER_MARKER]: true;
  [HANDLER_DEBOUNCE]?: number;
  [HANDLER_THROTTLE]?: number;
};

/**
 * Returns the debounce value (in milliseconds) to use as the default for a user
 * input element when no user input has been recorded yet. Uses the maximum
 * debounce among the element's tagged handlers, falling back to the global
 * default if none of the handlers specify one.
 */
export function getInitialDebounce(
  props: Record<string, unknown>,
  fallback: number,
): number {
  let max = 0;
  for (const value of Object.values(props)) {
    if (typeof value !== "function") {
      continue;
    }
    const candidate = (value as TaggedEventHandler)[HANDLER_DEBOUNCE];
    if (typeof candidate === "number" && candidate > max) {
      max = candidate;
    }
  }
  return max > 0 ? max : fallback;
}

/**
 * Returns true when the given value is a finite, non-negative integer.
 * Used to validate debounce/throttle values arriving over the wire from the
 * Python layout.
 */
export function isValidDebounce(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    Number.isInteger(value) &&
    value >= 0
  );
}

export const isValidThrottle = isValidDebounce;
