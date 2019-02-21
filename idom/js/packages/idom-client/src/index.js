import React from 'react';
import ReactDOM from 'react-dom';
import Layout from 'idom-layout';

const socket = new WebSocket("ws://localhost:8765/stream")
const layout = <Layout socket={ socket } />
ReactDOM.render(layout, document.getElementById('root'));
