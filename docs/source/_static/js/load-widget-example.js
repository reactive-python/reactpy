const IDOM_CLIENT_REACT_PATH = "/client/_snowpack/pkg/idom-client-react.js";

export default function loadWidgetExample(
  idomServerHost,
  idomServerPath,
  mountID,
  viewID
) {
  const loc = window.location;
  const idom_url = "//" + (idomServerHost || loc.host) + idomServerPath;
  const http_proto = loc.protocol;
  const ws_proto = http_proto === "https:" ? "wss:" : "ws:";

  const mount = document.getElementById(mountID);
  const enableWidgetButton = document.createElement("button");
  enableWidgetButton.innerHTML = "Enable Widget";
  enableWidgetButton.setAttribute("class", "enable-widget-button");

  enableWidgetButton.addEventListener("click", () => {
    {
      import(http_proto + idom_url + IDOM_CLIENT_REACT_PATH).then((module) => {
        {
          fadeOutAndThen(enableWidgetButton, () => {
            {
              mount.removeChild(enableWidgetButton);
              mount.setAttribute("class", "interactive widget-container");
              module.mountLayoutWithWebSocket(
                mount,
                ws_proto + idom_url + `/stream?view_id=${viewID}`
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

  mount.appendChild(enableWidgetButton);
}
