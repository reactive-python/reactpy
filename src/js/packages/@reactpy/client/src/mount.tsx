import React from "preact/compat";
import { render } from "preact/compat";
import { Layout } from "./components";
import { ReactPyClient } from "./reactpy-client";

export function mount(element: HTMLElement, client: ReactPyClient): void {
  render(<Layout client={client} />, element);
}
