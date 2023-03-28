import React from "react";
import { render } from "react-dom";
import { Layout } from "./components";
import { ReactPyClient } from "./reactpy-client";

export function mount(element: HTMLElement, client: ReactPyClient): void {
  render(<Layout client={client} />, element);
}
