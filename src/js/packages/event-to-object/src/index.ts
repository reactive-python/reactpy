const maxDepthSignal = { __stop__: true };

/**
 * Convert any class object (such as `Event`) to a plain object.
 */
export default function convert(
  classObject: { [key: string]: any },
  maxDepth: number = 10,
): object {
  // Immediately return `classObject` if given an unexpected (non-object) input
  if (!classObject || typeof classObject !== "object") {
    console.warn(
      "eventToObject: Expected an object input, received:",
      classObject,
    );
    return classObject;
  }

  // Begin conversion
  const visited = new WeakSet<any>();
  visited.add(classObject);
  const convertedObj: { [key: string]: any } = {};
  for (const key in classObject) {
    // Skip keys that cannot be converted
    try {
      if (shouldIgnoreValue(classObject[key], key)) {
        continue;
      }
      // Handle objects (potentially cyclical)
      else if (typeof classObject[key] === "object") {
        const result = deepCloneClass(classObject[key], maxDepth, visited);
        if (result !== maxDepthSignal) {
          convertedObj[key] = result;
        }
      }
      // Handle simple types (non-cyclical)
      else {
        convertedObj[key] = classObject[key];
      }
    } catch {
      continue;
    }
  }

  // Special case: Event selection
  if (
    typeof window !== "undefined" &&
    window.Event &&
    classObject instanceof window.Event
  ) {
    convertedObj["selection"] = serializeSelection(maxDepth, visited);
  }

  return convertedObj;
}

/**
 * Serialize the current window selection.
 */
function serializeSelection(
  maxDepth: number,
  visited: WeakSet<any>,
): object | null {
  if (typeof window === "undefined" || !window.getSelection) {
    return null;
  }
  const selection = window.getSelection();
  if (!selection) {
    return null;
  }
  return {
    type: selection.type,
    anchorNode: selection.anchorNode
      ? deepCloneClass(selection.anchorNode, maxDepth, visited)
      : null,
    anchorOffset: selection.anchorOffset,
    focusNode: selection.focusNode
      ? deepCloneClass(selection.focusNode, maxDepth, visited)
      : null,
    focusOffset: selection.focusOffset,
    isCollapsed: selection.isCollapsed,
    rangeCount: selection.rangeCount,
    selectedText: selection.toString(),
  };
}

/**
 * Recursively convert a class-based object to a plain object.
 */
function deepCloneClass(
  x: any,
  _maxDepth: number,
  visited: WeakSet<any>,
): object {
  const maxDepth = _maxDepth - 1;

  // Return an indicator if maxDepth is reached
  if (maxDepth <= 0 && typeof x === "object") {
    return maxDepthSignal;
  }

  // Safety check: WeakSet only accepts objects (and not null)
  if (!x || typeof x !== "object") {
    return x;
  }

  if (visited.has(x)) {
    return maxDepthSignal;
  }
  visited.add(x);

  try {
    // Convert array-like class (e.g., NodeList, ClassList, HTMLCollection)
    if (
      Array.isArray(x) ||
      (typeof x?.length === "number" &&
        typeof x[Symbol.iterator] === "function" &&
        !Object.prototype.toString.call(x).includes("Map") &&
        !(x instanceof CSSStyleDeclaration))
    ) {
      return classToArray(x, maxDepth, visited);
    }

    // Convert mapping-like class (e.g., Node, Map, Set)
    return classToObject(x, maxDepth, visited);
  } finally {
    visited.delete(x);
  }
}

/**
 * Convert an array-like class to a plain array.
 */
function classToArray(
  x: any,
  maxDepth: number,
  visited: WeakSet<any>,
): Array<any> {
  const result: Array<any> = [];
  for (let i = 0; i < x.length; i++) {
    // Skip anything that should not be converted
    if (shouldIgnoreValue(x[i])) {
      continue;
    }
    // Only push objects as if we haven't reached max depth
    else if (typeof x[i] === "object") {
      const converted = deepCloneClass(x[i], maxDepth, visited);
      if (converted !== maxDepthSignal) {
        result.push(converted);
      }
    }
    // Add plain values if not skippable
    else {
      result.push(x[i]);
    }
  }
  return result;
}

/**
 * Convert a mapping-like class to a plain JSON object.
 * We must iterate through it with a for-loop in order to gain
 * access to properties from all parent classes.
 */
function classToObject(
  x: any,
  maxDepth: number,
  visited: WeakSet<any>,
): object {
  const result: { [key: string]: any } = {};
  for (const key in x) {
    try {
      // Skip anything that should not be converted
      if (shouldIgnoreValue(x[key], key, x)) {
        continue;
      }
      // Add objects as a property if we haven't reached max depth
      else if (typeof x[key] === "object") {
        const converted = deepCloneClass(x[key], maxDepth, visited);
        if (converted !== maxDepthSignal) {
          result[key] = converted;
        }
      }
      // Add plain values if not skippable
      else {
        result[key] = x[key];
      }
    } catch {
      continue;
    }
  }

  // Explicitly include dataset if it exists (it might not be enumerable)
  if (
    x &&
    typeof x === "object" &&
    "dataset" in x &&
    !Object.prototype.hasOwnProperty.call(result, "dataset")
  ) {
    const dataset = x["dataset"];
    if (!shouldIgnoreValue(dataset, "dataset", x)) {
      const converted = deepCloneClass(dataset, maxDepth, visited);
      if (converted !== maxDepthSignal) {
        result["dataset"] = converted;
      }
    }
  }

  // Explicitly include common input properties if they exist
  const extraProps = ["value", "checked", "files", "type", "name"];
  for (const prop of extraProps) {
    if (
      x &&
      typeof x === "object" &&
      prop in x &&
      !Object.prototype.hasOwnProperty.call(result, prop)
    ) {
      const val = x[prop];
      if (!shouldIgnoreValue(val, prop, x)) {
        if (typeof val === "object") {
          // Ensure files have enough depth to be serialized
          const propDepth = prop === "files" ? Math.max(maxDepth, 3) : maxDepth;
          const converted = deepCloneClass(val, propDepth, visited);
          if (converted !== maxDepthSignal) {
            result[prop] = converted;
          }
        } else {
          result[prop] = val;
        }
      }
    }
  }

  // Explicitly include form elements if they exist and are not enumerable
  const win = typeof window !== "undefined" ? window : undefined;
  // @ts-ignore
  const FormClass = win
    ? win.HTMLFormElement
    : typeof HTMLFormElement !== "undefined"
      ? HTMLFormElement
      : undefined;

  if (FormClass && x instanceof FormClass && x.elements) {
    for (let i = 0; i < x.elements.length; i++) {
      const element = x.elements[i] as any;
      if (
        element.name &&
        !Object.prototype.hasOwnProperty.call(result, element.name) &&
        !shouldIgnoreValue(element, element.name, x)
      ) {
        if (typeof element === "object") {
          const converted = deepCloneClass(element, maxDepth, visited);
          if (converted !== maxDepthSignal) {
            result[element.name] = converted;
          }
        } else {
          result[element.name] = element;
        }
      }
    }
  }

  return result;
}

/**
 * Check if a value is non-convertible or holds minimal value.
 */
function shouldIgnoreValue(
  value: any,
  keyName: string = "",
  parent: any = undefined,
): boolean {
  return (
    // Useless data
    value === null ||
    value === undefined ||
    keyName.startsWith("__") ||
    (keyName.length > 0 && /^[A-Z_]+$/.test(keyName)) ||
    // Non-convertible types
    typeof value === "function" ||
    value instanceof CSSStyleSheet ||
    value instanceof Window ||
    value instanceof Document ||
    keyName === "view" ||
    keyName === "size" ||
    keyName === "length" ||
    (parent instanceof CSSStyleDeclaration && value === "") ||
    // DOM Node Blacklist
    (typeof Node !== "undefined" &&
      parent instanceof Node &&
      // Recursive properties
      (keyName === "parentNode" ||
        keyName === "parentElement" ||
        keyName === "ownerDocument" ||
        keyName === "getRootNode" ||
        keyName === "childNodes" ||
        keyName === "children" ||
        keyName === "firstChild" ||
        keyName === "lastChild" ||
        keyName === "previousSibling" ||
        keyName === "nextSibling" ||
        keyName === "previousElementSibling" ||
        keyName === "nextElementSibling" ||
        // Potentially large data
        keyName === "innerHTML" ||
        keyName === "outerHTML" ||
        // Reflow triggers
        keyName === "offsetParent" ||
        keyName === "offsetWidth" ||
        keyName === "offsetHeight" ||
        keyName === "offsetLeft" ||
        keyName === "offsetTop" ||
        keyName === "clientTop" ||
        keyName === "clientLeft" ||
        keyName === "clientWidth" ||
        keyName === "clientHeight" ||
        keyName === "scrollWidth" ||
        keyName === "scrollHeight" ||
        keyName === "scrollTop" ||
        keyName === "scrollLeft"))
  );
}
