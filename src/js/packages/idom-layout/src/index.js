import React, { useReducer, useEffect, useState, useMemo } from "react";

const allUpdateTriggers = {};
const allModels = {};

function updateDynamicElement(elementId) {
    if (allUpdateTriggers.hasOwnProperty(elementId)) {
        allUpdateTriggers[elementId]();
    }
}

function Layout({ endpoint }) {
    const socket = useMemo(
        () => {
            return new WebSocket(endpoint);
        },
        [endpoint]
    );

    const [root, setRoot] = useState(null);

    socket.onmessage = event => {
        const msg = JSON.parse(event.data);
        Object.assign(allModels, msg.body.render.new);
        msg.body.render.old.forEach(elementId => {
            delete allModels[elementId];
        });
        msg.body.render.roots.forEach(updateDynamicElement);
        if (!root) {
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

    if (root) {
        return <DynamicElement elementId={root} sendEvent={sendEvent} />;
    } else {
        return <div />;
    }
}

function DynamicElement({ elementId, sendEvent }) {
    allUpdateTriggers[elementId] = useForceUpdate();
    const model = allModels[elementId];
    if ( model ) {
        return <Element model={model} sendEvent={sendEvent} />;
    } else {
        return <div/>;
    }
}

function Element({ model, sendEvent }) {
    let children;
    if (!model.children) {
        children = [];
    } else {
        children = model.children.map(child => {
            switch (child.type) {
                case "ref":
                    return (
                        <DynamicElement
                            elementId={child.data}
                            sendEvent={sendEvent}
                        />
                    );
                case "obj":
                    return <Element model={child.data} sendEvent={sendEvent} />;
                case "str":
                    return child.data;
            }
        });
    }

    const attributes = Object.assign({}, model.attributes);

    if (model.eventHandlers) {
        Object.keys(model.eventHandlers).forEach(eventName => {
            const eventSpec = model.eventHandlers[eventName];
            attributes[eventName] = event => {
                if (eventSpec["preventDefault"]) {
                    event.preventDefault();
                }
                if (eventSpec["stopPropagation"]) {
                    event.stopPropagation();
                }
                const sentEvent = new Promise(
                    (resolve, reject) => {
                        const data = {};
                        if (eventSpec["eventProps"]) {
                            eventSpec["eventProps"].forEach(prop => {
                                data[prop] = getPathProperty(event, prop);
                            });
                        }
                        const msg = {
                            target: eventSpec["target"],
                            data: data
                        }
                        sendEvent(msg);
                        resolve(msg);
                    }
                );
            };
        });
    }

    let Tag = model.tagName;
    if (children.length) {
        return <Tag {...attributes}>{children}</Tag>;
    } else {
        return <Tag {...attributes} />;
    }
}

function useForceUpdate() {
    const [, setState] = useState(true);
    const forceUpdate = () => {
        setState(state => !state);
    };
    return forceUpdate;
}


function getPathProperty(obj, prop) {
    // properties may be dot seperated strings
    const path = prop.split(".");
    const firstProp = path.shift();
    let value = obj[firstProp];
    for (let i = 0; i < path.length; i++) {
        value = value[path[i]];
    }
    return value
}


export default Layout;
