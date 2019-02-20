import React, { useReducer, useEffect, useState, useMemo } from 'react';
import produce from 'immer';

function Layout(endpoint) {
    const [root, setRoot] = useState(null);
    const [models, setModels] = useState({});

    const sendMsg = useSocket(
        endpoint,
        {
            header: {
                status: 'ok',
                type: 'handshake'
            },
            body: {
                user: 'test',
                pass: 'test'
            }
        },
        function onMsg(msg) {
            setModels(
                produce(models, draftModels => {
                    Object.assign(draftModels, msg.body.models);
                })
            );
        }
    );

    if (root == null) {
        return <div />;
    } else {
        return Element(models, id, event => {
            sendMsg({
                header: {
                    status: 'ok'
                }
            });
        });
    }
}

function Element(models, id, sendEvent) {
    const model = models[id];

    const children = useMemo(
        () => {
            model.children.map(child => {
                switch (child.type) {
                    case 'ref':
                        return Element(models[child.data]);
                    case 'obj':
                        return Element(child.data);
                    case 'str':
                        return child.data;
                }
            });
        },
        [model.children]
    );

    const attributes = Object.assign({}, model.attributes);

    Object.keys(model.eventHandlers).forEach(target => {
        const [handler, eventName] = model.eventHandlers[key].split('_', 1);
        attributes[eventName] = event => {
            sendEvent({
                target: target,
                hander: handler,
                data: event
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

function useSocket(uri, firstSend, onMsg) {
    const [socket, setSocket] = useState(null);

    useEffect(
        () => {
            ws = new WebSocket(uri);
            ws.onopen = () => {
                ws.send(JSON.stringify(firstSend));
            };
            ws.onmessage = event => {
                onMsg(JSON.parse(event.data));
            };
            setSocket(ws);
            return ws.close;
        },
        [uri, firstSend, onMsg]
    );

    function send(data) {
        socket.send(JSON.stringify(data));
    }

    function setOnMsg(onMsg) {
        socket.onmessage = event => {
            onMsg(JSON.parse(event.data));
        };
    }

    return [send, setOnMsg];
}

export default Layout;
