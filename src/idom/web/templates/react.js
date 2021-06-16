export * from "$CDN/$PACKAGE";

import * as react from "$CDN/react";
import * as reactDOM from "$CDN/react-dom";

export const createElement = (component, props) =>
  react.createElement(component, props);
export const renderElement = reactDOM.render;
export const unmountElement = reactDOM.unmountComponentAtNode;
