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

export type ReconnectingCheckMessage = {
  type: "reconnecting-check";
  value: string;
}

export type IncomingMessage = LayoutUpdateMessage | ReconnectingCheckMessage;
export type OutgoingMessage = LayoutEventMessage | ReconnectingCheckMessage;
export type Message = IncomingMessage | OutgoingMessage;
