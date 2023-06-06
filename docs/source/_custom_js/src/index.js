import { SimpleReactPyClient, mount } from "@reactpy/client";

let didMountDebug = false;

export function mountWidgetExample(
  mountID,
  viewID,
  reactpyServerHost,
  useActivateButton,
) {
  let reactpyHost, reactpyPort;
  if (reactpyServerHost) {
    [reactpyHost, reactpyPort] = reactpyServerHost.split(":", 2);
  } else {
    reactpyHost = window.location.hostname;
    reactpyPort = window.location.port;
  }

  const client = new SimpleReactPyClient({
    serverLocation: {
      url: `${window.location.protocol}//${reactpyHost}:${reactpyPort}`,
      route: "/",
      query: `?view_id=${viewID}`,
    },
  });

  const mountEl = document.getElementById(mountID);
  let isMounted = false;
  triggerIfInViewport(mountEl, () => {
    if (!isMounted) {
      activateView(mountEl, client, useActivateButton);
      isMounted = true;
    }
  });
}

function activateView(mountEl, client, useActivateButton) {
  if (!useActivateButton) {
    mount(mountEl, client);
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
    }),
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
      threshold: 0.1, // set offset 0.1 means trigger if at least 10% of element in viewport
    },
  );

  observer.observe(element);
}
