import React, {
    useReducer,
    useEffect,
    useState,
    useMemo,
    Suspense
} from "../web_modules/react.js";
import htm from '../web_modules/htm.js'
import serializeEvent from "./event-to-object.js";

const html = htm.bind(React.createElement);

const allUpdateTriggers = {};
const allModels = {};

function updateDynamicElement(elementId) {
    if (allUpdateTriggers.hasOwnProperty(elementId)) {
        allUpdateTriggers[elementId]();
    }
}

function Layout({ endpoint }) {
    // handle relative endpoint URI
    if (endpoint.startsWith(".") || endpoint.startsWith("/")) {
        let loc = window.location;
        let protocol;
        if (loc.protocol === "https:") {
            protocol = "wss:";
        } else {
            protocol = "ws:";
        }
        let new_uri = protocol + "//" + loc.host;
        if (endpoint.startsWith(".")) {
            new_url += loc.pathname + "/";
        }
        endpoint = new_uri + endpoint;
    }

    const socket = useMemo(() => {
        return new WebSocket(endpoint);
    }, [endpoint]);

    const [root, setRoot] = useState(null);

    socket.onmessage = event => {
        const msg = JSON.parse(event.data);
        Object.assign(allModels, msg.body.render.new);
        msg.body.render.old.forEach(elementId => {
            delete allModels[elementId];
        });
        updateDynamicElement(msg.body.render.src);
        if (!root) {
            setRoot(msg.body.render.root);
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
        return html`<DynamicElement elementId={root} sendEvent={sendEvent} />`;
    } else {
        return html`<div />`;
    }
}

function DynamicElement({ elementId, sendEvent }) {
    allUpdateTriggers[elementId] = useForceUpdate();
    const model = allModels[elementId];
    if (model) {
        return html`<Element model={model} sendEvent={sendEvent} />`;
    } else {
        return html`<div />`;
    }
}

function Element({ model, sendEvent }) {
    const children = elementChildren(model, sendEvent);
    const attributes = elementAttributes(model, sendEvent);
    if (model.importSource) {
        const lazy = lazyComponent(model);
        return html`
            <Suspense fallback={model.importSource.fallback}>
                {React.createElement(lazy, attributes, children)}
            </Suspense>
        `;
    } else if (model.children && model.children.length) {
        return React.createElement(model.tagName, attributes, children);
    } else {
        return React.createElement(model.tagName, attributes);
    }
}

function elementChildren(model, sendEvent) {
    if (!model.children) {
        return [];
    } else {
        return model.children.map(child => {
            switch (child.type) {
                case "ref":
                    return html`
                        <DynamicElement
                            elementId={child.data}
                            sendEvent={sendEvent}
                        />
                    `;
                case "obj":
                    return html`<Element model={child.data} sendEvent={sendEvent} />`;
                case "str":
                    return child.data;
            }
        });
    }
}

function elementAttributes(model, sendEvent) {
    const attributes = Object.assign({}, model.attributes);

    if (model.eventHandlers) {
        Object.keys(model.eventHandlers).forEach(eventName => {
            const eventSpec = model.eventHandlers[eventName];
            attributes[eventName] = function(event) {
                const data = Array.from(arguments).map(value => {
                    if (typeof value === "object" && value.nativeEvent) {
                        if (eventSpec["preventDefault"]) {
                            value.preventDefault();
                        }
                        if (eventSpec["stopPropagation"]) {
                            value.stopPropagation();
                        }
                        return serializeEvent(value);
                    } else {
                        return value;
                    }
                });
                const sentEvent = new Promise((resolve, reject) => {
                    const msg = {
                        data: data,
                        target: eventSpec["target"]
                    };
                    sendEvent(msg);
                    resolve(msg);
                });
            };
        });
    }

    return attributes;
}
function useForceUpdate() {
    const [, setState] = useState(true);
    const forceUpdate = () => {
        setState(state => !state);
    };
    return forceUpdate;
}

export default Layout;
