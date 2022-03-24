import { mountWithLayoutServer, LayoutServerInfo } from "idom-client-react";

export function mount(mountPoint) {
  console.log("Mounted");
  const serverInfo = new LayoutServerInfo({
    host: document.location.hostname,
    port: document.location.port,
    path: "../",
    query: queryParams.user.toString(),
    secure: document.location.protocol == "https",
  });
  console.log(document.location.protocol)
  mountWithLayoutServer(mountPoint, serverInfo, shouldReconnect() ? 45 : 0);
}

function shouldReconnect() {
  return queryParams.reserved.get("noReconnect") === null;
}

const queryParams = (() => {
  const reservedParams = new URLSearchParams();
  const userParams = new URLSearchParams(window.location.search);

  const reservedParamNames = ["noReconnect"];
  reservedParamNames.forEach((name) => {
    const value = userParams.get(name);
    if (value !== null) {
      reservedParams.append(name, userParams.get(name));
      userParams.delete(name);
    }
  });

  return {
    reserved: reservedParams,
    user: userParams,
  };
})();
