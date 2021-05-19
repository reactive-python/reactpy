import { test } from "uvu";
import { JSDOM } from "jsdom";

const { window } = new JSDOM("<main></main>");

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
}

test.before(setup);
test.before.each(reset);
