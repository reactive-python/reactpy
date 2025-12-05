const maxDepthSignal = { __stop__: true };

/**
 * Convert any class object (such as `Event`) to a plain object.
 */
export function convert(
  classObject: { [key: string]: any },
  maxDepth: number = 3,
): object {
  // Begin conversion
  const convertedObj: { [key: string]: any } = {};
  for (const key in classObject) {
    // Skip keys that cannot be converted
    if (shouldIgnoreValue(classObject[key], key)) {
      continue;
    }
    // Handle objects (potentially cyclical)
    else if (typeof classObject[key] === "object") {
      const result = deepCloneClass(classObject[key], maxDepth);
      convertedObj[key] = result;
    }
    // Handle simple types (non-cyclical)
    else {
      convertedObj[key] = classObject[key];
    }
  }

  // Special case: Event selection
  if (
    typeof window !== "undefined" &&
    window.Event &&
    classObject instanceof window.Event
  ) {
    convertedObj["selection"] = serializeSelection(maxDepth);
  }

  return convertedObj;
}

/**
 * Serialize the current window selection.
 */
function serializeSelection(maxDepth: number): object | null {
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
      ? deepCloneClass(selection.anchorNode, maxDepth)
      : null,
    anchorOffset: selection.anchorOffset,
    focusNode: selection.focusNode
      ? deepCloneClass(selection.focusNode, maxDepth)
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
function deepCloneClass(x: any, _maxDepth: number): object {
  const maxDepth = _maxDepth - 1;

  // Return an indicator if maxDepth is reached
  if (maxDepth <= 0 && typeof x === "object") {
    return maxDepthSignal;
  }

  // Convert array-like class (e.g., NodeList, ClassList, HTMLCollection)
  if (
    Array.isArray(x) ||
    (typeof x?.length === "number" &&
      typeof x[Symbol.iterator] === "function" &&
      !Object.prototype.toString.call(x).includes("Map") &&
      !(x instanceof CSSStyleDeclaration))
  ) {
    return classToArray(x, maxDepth);
  }

  // Convert mapping-like class (e.g., Node, Map, Set)
  return classToObject(x, maxDepth);
}

/**
 * Convert an array-like class to a plain array.
 */
function classToArray(x: any, maxDepth: number): Array<any> {
  const result: Array<any> = [];
  for (let i = 0; i < x.length; i++) {
    // Skip anything that should not be converted
    if (shouldIgnoreValue(x[i])) {
      continue;
    }
    // Only push objects as if we haven't reached max depth
    else if (typeof x[i] === "object") {
      const converted = deepCloneClass(x[i], maxDepth);
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
function classToObject(x: any, maxDepth: number): object {
  const result: { [key: string]: any } = {};
  for (const key in x) {
    // Skip anything that should not be converted
    if (shouldIgnoreValue(x[key], key, x)) {
      continue;
    }
    // Add objects as a property if we haven't reached max depth
    else if (typeof x[key] === "object") {
      const converted = deepCloneClass(x[key], maxDepth);
      if (converted !== maxDepthSignal) {
        result[key] = converted;
      }
    }
    // Add plain values if not skippable
    else {
      result[key] = x[key];
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
    value === null ||
    value === undefined ||
    typeof value === "function" ||
    value instanceof CSSStyleSheet ||
    value instanceof Window ||
    value instanceof Document ||
    keyName === "view" ||
    keyName === "size" ||
    keyName === "length" ||
    (keyName.length > 0 && keyName.toUpperCase() === keyName) ||
    keyName.startsWith("__") ||
    (parent instanceof CSSStyleDeclaration && value === "")
  );
}
