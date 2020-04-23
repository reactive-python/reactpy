import React from "./react.js";
import { VictoryBar, VictoryChart, VictoryTheme, Bar } from "./victory.js";
import htm from "./htm.js";

const html = htm.bind(React.createElement);

export default {
  ClickableChart: function ClickableChart(props) {
    return html`
      <${VictoryChart}
        theme=${VictoryTheme.material}
        style=${props.style}
        domainPadding=${20}
      >
        <${VictoryBar}
          data=${[
            { x: 1, y: 2 },
            { x: 2, y: 4 },
            { x: 3, y: 7 },
            { x: 4, y: 3 },
            { x: 5, y: 5 },
          ]}
          dataComponent=${html`
            <${Bar}
              events=${{
                onClick: props.onClick,
              }}
            />
          `}
        />
      <//>
    `;
  },
};
