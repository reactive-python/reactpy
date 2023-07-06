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

export type LocalStorageUpdateMessage = {
  type: "sync-local-storage",
  storage: any;
}

export type SessionStorageUpdateMessage = {
  type: "sync-session-storage",
  storage: any;
}

export type IncomingMessage = LayoutUpdateMessage | LocalStorageUpdateMessage | SessionStorageUpdateMessage;
export type OutgoingMessage = LayoutEventMessage | LocalStorageUpdateMessage | SessionStorageUpdateMessage;
export type Message = IncomingMessage | OutgoingMessage;
