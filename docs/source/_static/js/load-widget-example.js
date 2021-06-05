const LOC = window.location;
const HTTP_PROTO = LOC.protocol;
const WS_PROTO = HTTP_PROTO === "https:" ? "wss:" : "ws:";
const IDOM_MODULES_PATH = "/_modules";
const IDOM_CLIENT_REACT_PATH = IDOM_MODULES_PATH + "/idom-client-react.js";

export default function loadWidgetExample(idomServerHost, mountID, viewID) {
  const idom_url = "//" + (idomServerHost || LOC.host);
  const http_idom_url = HTTP_PROTO + idom_url;
  const ws_idom_url = WS_PROTO + idom_url;

  const mountEl = document.getElementById(mountID);
  const enableWidgetButton = document.createElement("button");
  enableWidgetButton.appendChild(document.createTextNode("Enable Widget"));
  enableWidgetButton.setAttribute("class", "enable-widget-button");

  enableWidgetButton.addEventListener("click", () => {
    {
      import(http_idom_url + IDOM_CLIENT_REACT_PATH).then((module) => {
        {
          fadeOutAndThen(enableWidgetButton, () => {
            {
              mountEl.removeChild(enableWidgetButton);
              mountEl.setAttribute("class", "interactive widget-container");
              module.mountLayoutWithWebSocket(
                mountEl,
                ws_idom_url + `/_idom/stream?view_id=${viewID}`,
                (source, sourceType) =>
                  loadImportSource(http_idom_url, source, sourceType)
              );
            }
          });
        }
      });
    }
  });

  function fadeOutAndThen(element, callback) {
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
    return import(baseUrl + IDOM_MODULES_PATH + "/" + source + ".js");
  } else {
    return import(source);
  }
}
