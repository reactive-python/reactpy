import React, { useReducer, useEffect, useState, useMemo } from "react";
import $ from 'jquery';

const allUpdateTriggers = {};
const allModels = {};

function updateDynamicElement(elementId) {
    if (allUpdateTriggers.hasOwnProperty(elementId)) {
        allUpdateTriggers[elementId]();
    }
}

function Layout({ endpoint }) {
    const socket = useMemo(() => {
        return new WebSocket(endpoint);
      },
      [endpoint]
    );

    const [root, setRoot] = useState(null);

    socket.onmessage = event => {
        const msg = JSON.parse(event.data);
        Object.assign(allModels, msg.body.render.new)
        msg.body.render.old.forEach(elementId => { delete allModels[elementId] });
        msg.body.render.roots.forEach(updateDynamicElement);
        if ( !root ) {
            setRoot(msg.body.render.roots[0]);
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

    if ( root ){
        return <DynamicElement elementId={root} sendEvent={sendEvent}/>;
    } else {
        return <div />;
    }
}

function DynamicElement({ elementId, sendEvent }) {
    allUpdateTriggers[elementId] = useForceUpdate();
    const model = allModels[elementId];
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
        const [handler, eventDef] = model.eventHandlers[target].split(/_(.+)/);
        const eventDataSpec = eventDef.split("-");
        const eventName = eventDataSpec.shift();
        attributes[eventName] = event => {
            const data = {};
            eventDataSpec.forEach(n => {
                if ( event.hasOwnProperty(n) ) {
                    data[n] = event[n];
                } else {
                    data[n] = event.target[n];
                }
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
