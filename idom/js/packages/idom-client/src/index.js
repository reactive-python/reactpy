import React from 'react';
import ReactDOM from 'react-dom';
import Layout from 'idom-layout';

ReactDOM.render(
    <Layout endpoint="wss://localhost:8765/" />,
    document.getElementById('root')
);
