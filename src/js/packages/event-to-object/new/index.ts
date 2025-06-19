// Note, the build command is: bun build index.ts --outfile=index.js
// TODO: Test this with file uploads, form events, and other complex event types.
// TODO: Investigate these potentially useful libraries:
//       https://www.npmjs.com/package/superserial#circular-reference
//       https://www.npmjs.com/package/@badcafe/jsonizer
//       https://www.npmjs.com/package/class-transformer#how-does-it-handle-circular-references
//       https://www.npmjs.com/package/compress-json

const stopSignal = { __stop__: true };

/**
 * Convert any object to a plain object.
 */
function convert(object: object, maxDepth: number = 3): object {
  // Begin conversion
  const convertedObj = {};
  for (const key in object) {
    // Skip keys that cannot be converted
    if (shouldIgnore(object[key], key)) {
      continue;
    }
    // Handle objects (potentially cyclical)
    else if (typeof object[key] === "object") {
      const result = deepClone(object[key], maxDepth);
      convertedObj[key] = result;
    }
    // Handle simple types (non-cyclical)
    else {
      convertedObj[key] = object[key];
    }
  }
  return convertedObj;
}

/**
 * Recursively convert a complex object to a plain object.
 */
function deepClone(x: any, _maxDepth: number): object {
  const maxDepth = _maxDepth - 1;

  // Return an indicator if maxDepth is reached
  if (maxDepth <= 0 && typeof x === "object") {
    return stopSignal;
  }

  // Return early if already a plain object
  if (isPlainObject(x)) {
    return x;
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
    // Skip keys that cannot be converted
    if (shouldIgnore(x[i])) {
      continue;
    }
    // Only push objects as if we haven't reached max depth
    else if (typeof x[i] === "object") {
      const convertedItem = deepClone(x[i], maxDepth);
      if (convertedItem !== stopSignal) {
        result.push(convertedItem);
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
 */
function classToObject(x: any, maxDepth: number): object {
  const result = {};
  for (const key in x) {
    // Skip keys that cannot be converted
    if (shouldIgnore(x[key], key, x)) {
      continue;
    }
    // Add objects as a property if we haven't reached max depth
    else if (typeof x[key] === "object") {
      const convertedObj = deepClone(x[key], maxDepth);
      if (convertedObj !== stopSignal) {
        result[key] = convertedObj;
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
function shouldIgnore(
  value: any,
  keyName: string = "",
  parent: any = undefined,
): boolean {
  return (
    value === null ||
    value === undefined ||
    // value === "" ||
    typeof value === "function" ||
    value instanceof CSSStyleSheet ||
    value instanceof Window ||
    value instanceof Document ||
    keyName === "view" ||
    keyName === "size" ||
    keyName === "length" ||
    keyName.toUpperCase() === keyName ||
    (parent instanceof CSSStyleDeclaration && value === "")
  );
}

/**
 * Check if an object is a plain object.
 * A plain object is an object created by `Object()` or squiggly braces `{}`. Additionally,
 * `null` is treated as a plain object.
 */
function isPlainObject(x: any): boolean {
  if (typeof x !== "object" || x === null) {
    return false;
  }
  const proto = Object.getPrototypeOf(x);
  return proto === Object.prototype || proto === null;
}

// /**
//  * Get the class name of an object.
//  */
// function getClassName(obj: object): string {
//   return Function.prototype.call.bind(Object.prototype.toString)(obj);
// }
//
// /**
//  * Get the index of an object in a set, or -1 if not found.
//  */
// function getObjectIndex(obj: object, set: Set<object>): number {
//   // Try to find the object by comparing JSON representation
//   let index = 0;
//   for (const item of set) {
//     if (
//       typeof item === "object" &&
//       getClassName(item) === getClassName(obj) &&
//       JSON.stringify(item) == JSON.stringify(obj)
//     ) {
//       return index;
//     }
//     index++;
//   }
//
//   // If the object is not found in the set, return -1
//   return -1;
// }

// Example usage of the convert function
var my_event = null;
function my_click(event) {
  my_event = event;
  console.log("Original Event:", event);
  const jsonEvent = convert(event);
  console.log("Converted Event:", JSON.stringify(jsonEvent, null, 2));
  console.log(
    "Byte Length:",
    new TextEncoder().encode(JSON.stringify(jsonEvent)).length,
  );
}
document
  .getElementById("fetchData")
  ?.addEventListener("click", my_click, false);
