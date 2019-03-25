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
    return <Element model={model} sendEvent={sendEvent} />;
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
        Object.keys(model.eventHandlers).forEach(target => {
            const eventSpec = model.eventHandlers[target].split("_");
            const [handlerId, eventName, eventProps] = eventSpec;
            attributes[eventName] = event => {
                const data = {};
                eventProps.split(";").forEach(prop => {
                    const path = prop.split(".");
                    const firstProp = path.shift();
                    let value = event[firstProp];
                    for (let i = 0; i < path.length; i++) {
                        value = value[path[i]];
                    }
                    data[prop] = value;
                });
                sendEvent({
                    target: target,
                    handler: model.eventHandlers[target],
                    data: data
                });
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

export default Layout;
