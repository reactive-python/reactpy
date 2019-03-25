import React from "react";
import ReactDOM from "react-dom";
import Layout from "idom-layout";
import "./index.css";

const uri = document.location.hostname + ":" + document.location.port;
const url = (uri + document.location.pathname).split("/").slice(0, -1);
url[url.length - 1] = "stream";
const secure = document.location.protocol === "https:";

let protocol;
if (secure) {
    protocol = "wss:";
} else {
    protocol = "ws:";
}
let endpoint = protocol + "//" + url.join("/");

const mount = document.getElementById("root");
ReactDOM.render(<Layout endpoint={endpoint} />, mount);
