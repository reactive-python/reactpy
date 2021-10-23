import { mountLayoutWithWebSocket } from "idom-client-react";

const LOC = window.location;
const HTTP_PROTO = LOC.protocol;
const WS_PROTO = HTTP_PROTO === "https:" ? "wss:" : "ws:";
const IDOM_MODULES_PATH = "/_modules";

export function mountWidgetExample(
  mountID,
  viewID,
  idomServerHost,
  useActivateButton
) {
  const idomUrl  = "//" + (idomServerHost || LOC.host);
  const httpIdomUrl = HTTP_PROTO + idomUrl ;
  const wsIdomUrl = WS_PROTO + idomUrl ;

  const mountEl = document.getElementById(mountID);

  if (!useActivateButton) {
    mountLayoutWithWebSocket(
      mountEl,
      wsIdomUrl + `/_idom/stream?view_id=${viewID}`,
      (source, sourceType) =>
        loadImportSource(httpIdomUrl, source, sourceType)
    );
    return;
  }

  const enableWidgetButton = document.createElement("button");
  enableWidgetButton.appendChild(document.createTextNode("Enable Widget"));
  enableWidgetButton.setAttribute("class", "enable-widget-button");

  enableWidgetButton.addEventListener("click", () =>
    fadeOutElementThenCallback(enableWidgetButton, () => {
      {
        mountEl.removeChild(enableWidgetButton);
        mountEl.setAttribute("class", "interactive widget-container");
        mountLayoutWithWebSocket(
          mountEl,
          wsIdomUrl + `/_idom/stream?view_id=${viewID}`,
          (source, sourceType) =>
            loadImportSource(httpIdomUrl, source, sourceType)
        );
      }
    })
  );

  function fadeOutElementThenCallback(element, callback) {
    {
      var op = 1; // initial opacity
      var timer = setInterval(function () {
        {
          if (op < 0.001) {
            {
              clearInterval(timer);
              element.style.display = "none";
              callback();
            }
          }
          element.style.opacity = op;
          element.style.filter = "alpha(opacity=" + op * 100 + ")";
          op -= op * 0.5;
        }
      }, 50);
    }
  }

  mountEl.appendChild(enableWidgetButton);
}

function loadImportSource(baseUrl, source, sourceType) {
  if (sourceType == "NAME") {
    return import(baseUrl + IDOM_MODULES_PATH + "/" + source);
  } else {
    return import(source);
  }
}
