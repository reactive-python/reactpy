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
  /** Current value of this handler's outgoing sequence counter */
  _reactpy_peek_seq?: () => number;
  /** Force the counter so the next dispatch carries the given sequence number */
  _reactpy_set_seq?: (seq: number) => void;
  /**
   * Called by the send path with the sequence number that was actually written
   * to the wire. A debounced handler allocates a sequence per keystroke but only
   * dispatches the last one, so anything which needs to know what the server has
   * genuinely been given has to be told here rather than guessing from how many
   * times the handler was called.
   */
  _reactpy_mark_sent?: (seq: number) => void;
};

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
