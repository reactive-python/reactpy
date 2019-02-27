import React, { useReducer, useEffect, useState, useMemo } from "react";
import produce from "immer";

const dynamicElements = {};
const allModels = {};

function Layout({ endpoint }) {
    const socket = useMemo(() => {
        return new WebSocket(endpoint);
      },
      [endpoint]
    );

    const [root, setRoot] = useState(null);

    socket.onmessage = event => {
        const msg = JSON.parse(event.data);
        Object.assign(allModels, msg.body.models)
        msg.body.updateRoots.forEach(elementId => {
            if (dynamicElements.hasOwnProperty(elementId)) {
                dynamicElements[elementId]();
            }
        });
        if (allModels.hasOwnProperty(msg.header.root) && msg.header.root != root) {
            setRoot(msg.header.root);
        }
    };

    const sendMsg = msg => {
        socket.send(JSON.stringify(msg));
    };
    const sendEvent = event => {
        sendMsg({
            header: {},
            body: { event: event }
        });
    };

    if (!allModels.hasOwnProperty(root)) {
        return <div />;
    } else {
        return <DynamicElement elementId={root} sendEvent={sendEvent}/>;
    }
}

function DynamicElement({ elementId, sendEvent}) {
    dynamicElements[elementId] = useForceUpdate()
    const model = allModels[elementId]
    return <Element model={model} sendEvent={sendEvent}/>;
}

function Element({ model, sendEvent }) {
    const children = model.children.map(child => {
        switch (child.type) {
            case "ref":
                return <DynamicElement elementId={child.data} sendEvent={sendEvent}/>;
            case "obj":
                return <Element model={child.data} sendEvent={sendEvent}/>;
            case "str":
                return child.data;
        }
    });

    const attributes = Object.assign({}, model.attributes);

    Object.keys(model.eventHandlers).forEach(target => {
        const [handler, eventDef] = model.eventHandlers[target].split("_");
        const eventParts = eventDef.split("-");
        const eventName = eventParts.shift();
        attributes[eventName] = event => {
            const data = {};
            eventParts.forEach(n => {
                data[n] = event[n];
            });
            sendEvent({
                target: target,
                handler: handler,
                data: data
            });
        };
    });

    let Tag = model.tagName;
    if (children.length) {
        return <Tag {...attributes}>{children}</Tag>;
    } else {
        return <Tag {...attributes} />;
    }
}

function useForceUpdate() {
  const [ , setState ] = useState(true);
  const forceUpdate = () => {
    setState(state => !state);
  };
  return forceUpdate;
}

export default Layout;
