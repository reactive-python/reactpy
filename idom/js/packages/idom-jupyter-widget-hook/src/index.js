import React from "react";
import ReactDOM from "react-dom";
import Layout from "idom-layout";

window.iDomWidgetMount = function iDomWidgetMount(endpoint, mountId) {
    const mount = document.getElementById(mountId);
    ReactDOM.render(<Layout endpoint={endpoint} />, mount);
};
