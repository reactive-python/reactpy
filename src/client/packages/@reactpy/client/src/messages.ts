import { ReactPyVdom } from "./reactpy-vdom";

export interface IMessage {
  type: string;
}

export type ConnectionOpenMessage = {
  type: "connection-open";
};

export type ConnectionCloseMessage = {
  type: "connection-close";
};

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

export type IncomingMessage =
  | LayoutUpdateMessage
  | ConnectionOpenMessage
  | ConnectionCloseMessage;
export type OutgoingMessage = LayoutEventMessage;
export type Message = IncomingMessage | OutgoingMessage;
