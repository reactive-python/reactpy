// Lazy, shared PyScript runtime for the docs "Run" tabs.
//
// Two properties matter, and both are load-bearing:
//
//  1. Nothing PyScript/Pyodide related is fetched at page load. A docs page
//     with eight demos costs exactly what a page with none costs.
//  2. One interpreter is shared by every demo on the page. The first demo pays
//     the Pyodide boot; every later one renders in ~0.1s instead of paying it
//     again (~3s each for the iframe-per-demo alternative).
//
// There is no Run button. Opening the tab *is* the request to execute, which is
// what a reader expects from a tab, and it keeps the panel free of chrome.
// Material's tabs are radios, and its tabs and panels are parallel lists, so a
// demo finds the radio that shows it and runs when that radio is checked.
//
// ReactPy's own `pyscript_setup_html` / `pyscript_executor_html` produce the
// pieces; `reactpy-run-config.js` is generated at build time from ReactPy
// itself, so this file never hard-codes a version, a URL, or the layout
// handler.

import { CONFIG_URL, RUNTIME } from '../reactpy-runtime/reactpy-run-config.js';

// Paths are relative to the *config* module, which sits next to the
// copied ReactPy static assets — not next to this file.
const STATIC_BASE = new URL(`${RUNTIME.staticRoot}/`, CONFIG_URL).href.replace(/\/+$/, '');

const url = (path) => `${STATIC_BASE}/${path}`;

/** PyScript resolves config URLs against the document, so expand them here. */
const pyscriptConfig = () =>
  RUNTIME.pyscriptConfig.replaceAll(RUNTIME.staticMarker, STATIC_BASE);

const state = { booted: false, queue: [], started: new Set() };

function loadSharedRuntime() {
  if (state.booted) return;
  state.booted = true;

  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = url('pyscript/core.css');
  document.head.append(css);

  // The shared interpreter's entry point: ReactPy's layout handler plus the
  // Pyodide package config, as one `<script type="py" config=...>`.
  const setup = document.createElement('script');
  setup.type = 'py';
  setup.setAttribute('config', pyscriptConfig());
  setup.textContent = RUNTIME.layoutHandler;
  document.body.append(setup);

  // PyScript scans the document for `type="py"` scripts when core.js runs, so
  // any demo queued before boot must be in the DOM *before* we add core.js.
  flushQueue();

  const core = document.createElement('script');
  core.type = 'module';
  core.async = true;
  core.crossOrigin = 'anonymous';
  core.src = url('pyscript/core.js');
  document.head.append(core);
}

function flushQueue() {
  while (state.queue.length) injectDemo(state.queue.shift());
}

function start(id) {
  if (state.started.has(id)) return;
  state.started.add(id);

  // Say *something* while Pyodide boots: an empty panel reads as a broken
  // page. The word lives in CSS, not the HTML, so it never reaches the search
  // index or a screen reader's read of the document.
  const panel = document.querySelector(`[data-reactpy-run="${id}"]`);
  if (panel) panel.dataset.reactpyState = 'booting';

  state.queue.push(id);
  if (state.booted) flushQueue();
  else loadSharedRuntime();
}

function injectDemo(id) {
  const template = document.getElementById(`reactpy-src-${id}`);
  const anchor = document.querySelector(`[data-reactpy-run="${id}"]`);
  if (!template || !anchor) {
    // A block the build could not fill in says so itself. Don't leave it
    // claiming to be booting.
    if (anchor) delete anchor.dataset.reactpyState;
    return;
  }

  for (const node of [...template.content.children]) {
    const clone = node.cloneNode(true);
    // Scoped `<style>`s belong in <head>; the `<script type="py">` has to be
    // in the document for PyScript's MutationObserver to pick it up.
    (clone.tagName === 'STYLE' ? document.head : anchor).append(clone);
  }

  watchForOutput(id, anchor);
}

function watchForOutput(id, anchor) {
  const output = anchor.querySelector('.reactpy-run-out');
  const status = anchor.querySelector('.reactpy-run-status');

  const done = () => {
    if (output.textContent.trim() || output.children.length) {
      observer.disconnect();
      clearTimeout(timeout);
      anchor.dataset.reactpyState = 'ready';
      if (status) status.hidden = true;
      return true;
    }
    return false;
  };
  const observer = new MutationObserver(done);
  observer.observe(output, { childList: true, subtree: true, characterData: true });
  // Silence is the only failure mode a reader can see, so say something before
  // they conclude the page is broken.
  const timeout = setTimeout(() => {
    observer.disconnect();
    if (!done() && status) {
      anchor.dataset.reactpyState = 'stalled';
      status.hidden = false;
      status.textContent = 'Still starting — check the browser console for errors.';
    }
  }, 30_000);
  done();
}

/**
 * The radio button that reveals *el*, or null when *el* is not in a tab set.
 *
 * Material emits `.tabbed-set` with N radios, then N labels, then a
 * `.tabbed-content` holding N `.tabbed-block` panels — two lists in the same
 * order, so position is the only thing linking a tab to its panel.
 */
function owningRadio(el) {
  const block = el.closest('.tabbed-block');
  const set = el.closest('.tabbed-set');
  if (!block || !set) return null;

  const panels = [...block.parentElement.children].filter((node) =>
    node.classList.contains('tabbed-block'),
  );
  const radios = [...set.children].filter(
    (node) => node.tagName === 'INPUT' && node.type === 'radio',
  );
  return radios[panels.indexOf(block)] ?? null;
}

/** Run *el* when the reader can see it: on tab change, or when scrolled to. */
function arm(el) {
  const id = el.dataset.reactpyRun;
  const radio = owningRadio(el);

  if (!radio) {
    // Not in a tab set (a hand-placed block). Boot when it enters the viewport
    // rather than at page load, which would fetch Pyodide for an unseen demo.
    const visible = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        visible.disconnect();
        start(id);
      }
    });
    visible.observe(el);
    return;
  }

  if (radio.checked) {
    start(id);
    return;
  }
  radio.addEventListener('change', () => start(id), { once: true });
}

const armAll = () => {
  for (const el of document.querySelectorAll('[data-reactpy-run]')) arm(el);
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', armAll);
} else {
  armAll();
}

// Warm the cache while the reader is idle, without ever executing Python.
if (RUNTIME.preload && 'requestIdleCallback' in window) {
  requestIdleCallback(
    () => {
      if (document.querySelector('[data-reactpy-run]')) {
        for (const asset of ['pyscript/core.js', 'pyscript/core.css']) {
          const link = document.createElement('link');
          link.rel = 'preload';
          link.as = asset.endsWith('.js') ? 'script' : 'style';
          link.href = url(asset);
          document.head.append(link);
        }
      }
    },
    { timeout: 4000 },
  );
}
