import { mountWithLayoutServer, LayoutServerInfo } from "idom-client-react";

let didMountDebug = false;

export function mountWidgetExample(
  mountID,
  viewID,
  idomServerHost,
  useActivateButton
) {
  let idomHost, idomPort;
  if (idomServerHost) {
    [idomHost, idomPort] = idomServerHost.split(":", 2);
  } else {
    idomHost = window.location.hostname;
    idomPort = window.location.port;
  }

  const serverInfo = new LayoutServerInfo({
    host: idomHost,
    port: idomPort,
    path: "/_idom/",
    query: `view_id=${viewID}`,
    secure: window.location.protocol == "https:",
  });

  const mountEl = document.getElementById(mountID);
  let isMounted = false;
  triggerIfInViewport(mountEl, () => {
    if (!isMounted) {
      activateView(mountEl, serverInfo, useActivateButton);
      isMounted = true;
    }
  });
}

function activateView(mountEl, serverInfo, useActivateButton) {
  if (!useActivateButton) {
    mountWithLayoutServer(mountEl, serverInfo);
    return;
  }

  const enableWidgetButton = document.createElement("button");
  enableWidgetButton.appendChild(document.createTextNode("Activate"));
  enableWidgetButton.setAttribute("class", "enable-widget-button");

  enableWidgetButton.addEventListener("click", () =>
    fadeOutElementThenCallback(enableWidgetButton, () => {
      {
        mountEl.removeChild(enableWidgetButton);
        mountEl.setAttribute("class", "interactive widget-container");
        mountWithLayoutServer(mountEl, serverInfo);
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

function triggerIfInViewport(element, callback) {
  const observer = new window.IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        callback();
      }
    },
    {
      root: null,
      threshold: 0.1, // set offset 0.1 means trigger if atleast 10% of element in viewport
    }
  );

  observer.observe(element);
}
