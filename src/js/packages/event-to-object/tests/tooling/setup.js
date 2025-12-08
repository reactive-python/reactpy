import { Window } from "happy-dom";
import { beforeAll, beforeEach } from "bun:test";

export const window = new Window();

export function setup() {
  global.window = window;
  global.document = window.document;
  global.navigator = window.navigator;
  global.getComputedStyle = window.getComputedStyle;
  global.requestAnimationFrame = null;
  global.CSSStyleSheet = window.CSSStyleSheet;
  global.CSSStyleDeclaration = window.CSSStyleDeclaration;
  global.Window = window.constructor;
  global.Document = window.document.constructor;
  global.Node = window.Node;
  global.Element = window.Element;
  global.HTMLElement = window.HTMLElement;
}

export function reset() {
  window.document.title = "";
  window.document.head.innerHTML = "";
  window.document.body.innerHTML = "<main></main>";
  window.getSelection().removeAllRanges();
}

beforeAll(setup);
beforeEach(reset);
