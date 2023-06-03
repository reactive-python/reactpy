import { test } from "uvu";
import { Window } from "happy-dom";

export const window = new Window();

export function setup() {
  global.window = window;
  global.document = window.document;
  global.navigator = window.navigator;
  global.getComputedStyle = window.getComputedStyle;
  global.requestAnimationFrame = null;
}

export function reset() {
  window.document.title = "";
  window.document.head.innerHTML = "";
  window.document.body.innerHTML = "<main></main>";
  window.getSelection().removeAllRanges();
}

test.before(setup);
test.before.each(reset);
