import { ReactPyVdom } from "./reactpy-vdom";

export type LayoutUpdateMessage = {
  type: "layout-update";
  path: string;
  model: ReactPyVdom;
};

export type LayoutEventMessage = {
  type: "layout-event";
  target: string;
  data: any;
};

export type IncomingMessage = LayoutUpdateMessage;
export type OutgoingMessage = LayoutEventMessage;
export type Message = IncomingMessage | OutgoingMessage;
