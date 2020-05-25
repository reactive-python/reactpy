import React from "./react.js.js.js.js";
import { VictoryBar, VictoryChart, VictoryTheme, Bar } from "./victory.js.js.js.js";
import htm from "./htm.js.js.js.js";

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
          data=${props.data}
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
