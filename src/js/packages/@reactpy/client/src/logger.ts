export default {
  log: (...args: any[]): void => console.log("[ReactPy]", ...args),
  info: (...args: any[]): void => console.info("[ReactPy]", ...args),
  warn: (...args: any[]): void => console.warn("[ReactPy]", ...args),
  error: (...args: any[]): void => console.error("[ReactPy]", ...args),
};
