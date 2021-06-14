// Copied from: https://developer.mozilla.org/en-US/docs/web/javascript/reference/statements/export

// Exporting individual features
export let name1, name2, name3; // also var, const
export let name4 = 4, name5 = 5, name6; // also var, const
export function functionName(){...}
export class ClassName {...}

// Export list
export { name7, name8, name9 };

// Renaming exports
export { variable1 as name10, variable2 as name11, name12 };

// Exporting destructured assignments with renaming
export const { name13, name14: bar } = o;

// Aggregating modules
export * from "source1"; // does not set the default export
export * from "source2"; // does not set the default export
export * as name15 from "source3"; // Draft ECMAScript® 2O21
export { name16, name17 } from "source4";
export { import1 as name18, import2 as name19, name20 } from "source5";
