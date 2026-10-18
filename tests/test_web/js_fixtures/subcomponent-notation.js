import React from "react";

const InputGroup = ({ children }) => React.createElement("div", { className: "input-group" }, children);
InputGroup.Text = ({ children, ...props }) => React.createElement("span", { className: "input-group-text", ...props }, children);

const Form = ({ children }) => React.createElement("form", {}, children);
Form.Control = ({ children, ...props }) => React.createElement("input", { className: "form-control", ...props }, children);
Form.Label = ({ children, ...props }) => React.createElement("label", { className: "form-label", ...props }, children);

export { InputGroup, Form };
