let dashboardData = null;


fetch("housing-dashboard-data.json")
  .then(response => response.json())
  .then(data => {
    dashboardData = data;
    initializeDashboard();
  })
  .catch(error => {
    console.error("Error loading dashboard data:", error);
  });

const stateSelect = document.getElementById("stateSelect");
const mapMetric = document.getElementById("mapMetric");
const dashboardNote = document.querySelector(".dashboard-note");


function initializeDashboard() {
  fillKpis();
  populateStateDropdown();
  renderMap(mapMetric.value);
  renderStateCharts(stateSelect.value || dashboardData.default_state);
  renderTable();
  renderInsights();
  updateDashboardNote(mapMetric.value);

  mapMetric.addEventListener("change", function () {
    const metric = this.value;
    renderMap(metric);
    updateDashboardNote(metric);
  });

  stateSelect.addEventListener("change", function () {
    renderStateCharts(this.value);
  });

  document.querySelectorAll("#state-table th[data-key]").forEach(header => {
  header.addEventListener("click", function () {
    const key = this.getAttribute("data-key");

    if (currentSortKey === key) {
      sortAscending = !sortAscending;
    } else {
      currentSortKey = key;
      sortAscending = true;
    }

    renderTable();
  });
});
}


function updateDashboardNote(metric) {
  if (!dashboardNote) return;

  if (metric === "affordability_change") {
    dashboardNote.innerHTML = `
      <strong>How to read the map:</strong><br>
      • This view shows the <strong>12-month affordability trend</strong><br>
      • Blue = affordability is improving<br>
      • Red = affordability is worsening
    `;
  } else if (metric === "forecast_affordability_ratio") {
    dashboardNote.innerHTML = `
      <strong>How to read the map:</strong><br>
      • This view shows the <strong>forecasted affordability ratio 12 months ahead</strong><br>
      • Higher affordability ratio = more affordable housing<br>
      • Blue = more affordable, Red = less affordable
    `;
  } else {
    dashboardNote.innerHTML = `
      <strong>How to read the map:</strong><br>
      • This view shows the <strong>current affordability ratio</strong><br>
      • Higher affordability ratio = more affordable housing<br>
      • Blue = more affordable, Red = less affordable
    `;
  }
}


function fillKpis() {
  document.getElementById("kpi-home-price").textContent =
    formatCurrency(dashboardData.kpis.current_home_price);

  document.getElementById("kpi-affordability").textContent =
    dashboardData.kpis.current_affordability_ratio.toFixed(2);

  document.getElementById("kpi-change").textContent =
    dashboardData.kpis.forecast_change.toFixed(2);

  document.getElementById("kpi-rate").textContent =
    dashboardData.kpis.mortgage_rate.toFixed(2) + "%";
}

function populateStateDropdown() {
  stateSelect.innerHTML = "";

  dashboardData.state_series.forEach(stateObj => {
    const option = document.createElement("option");
    option.value = stateObj.state;
    option.textContent = stateObj.state;
    if (stateObj.state === dashboardData.default_state) {
      option.selected = true;
    }
    stateSelect.appendChild(option);
  });
}

function renderMap(metricKey) {
  const states = dashboardData.map_data.map(d => d.state_code);
  console.log("STATE CODES:", states);
  const values = dashboardData.map_data.map(d => d[metricKey]);
  const isChangeView = metricKey === "affordability_change";
  const maxAbs = Math.max(...values.map(v => Math.abs(v || 0)));

  const hoverText = dashboardData.map_data.map(d =>
    `${d.state}<br>` +
    `Current Ratio: ${d.current_affordability_ratio.toFixed(2)}<br>` +
    `Forecast Ratio: ${d.forecast_affordability_ratio.toFixed(2)}<br>` +
    `Change: ${d.affordability_change.toFixed(2)}`
  );

  const data = [{
    type: "choropleth",
    locationmode: "USA-states",
    locations: states,
    z: values,
    text: hoverText,
    hoverinfo: "text",

  colorscale: [
  [0, "#dc2626"],
  [0.5, "#f3f4f6"],
  [1, "#2563eb"]
  ],
  marker: {
    line: {
      color: "white",
      width: 1
    }
  },
  colorbar: {
    title: metricKey.replaceAll("_", " ")
  }
}];

  const layout = {
    geo: {
      scope: "usa",
      bgcolor: "rgba(0,0,0,0)"
    },
    margin: { t: 10, r: 10, b: 10, l: 10 }
  };

  Plotly.newPlot("affordability-map", data, layout, { responsive: true });
}

function renderStateCharts(stateName) {
  const stateObj = dashboardData.state_series.find(d => d.state === stateName);
  if (!stateObj) return;

  const homePriceData = [
    {
      x: stateObj.history.map(d => d.date),
      y: stateObj.history.map(d => d.home_price),
      type: "scatter",
      mode: "lines",
      name: "Historical"
    },
    {
      x: stateObj.forecast.map(d => d.date),
      y: stateObj.forecast.map(d => d.home_price),
      type: "scatter",
      mode: "lines",
      name: "Forecast",
      line: { dash: "dash" }
    }
  ];

  const affordabilityData = [
    {
      x: stateObj.history.map(d => d.date),
      y: stateObj.history.map(d => d.affordability_ratio),
      type: "scatter",
      mode: "lines",
      name: "Historical"
    },
    {
      x: stateObj.forecast.map(d => d.date),
      y: stateObj.forecast.map(d => d.affordability_ratio),
      type: "scatter",
      mode: "lines",
      name: "Forecast",
      line: { dash: "dash" }
    }
  ];

  Plotly.newPlot(
    "home-price-chart",
    homePriceData,
    {
      margin: { t: 10, r: 10, b: 50, l: 60 },
      yaxis: { title: "Home Price" },
      xaxis: { title: "Date" }
    },
    { responsive: true }
  );

  Plotly.newPlot(
    "affordability-chart",
    affordabilityData,
    {
      margin: { t: 10, r: 10, b: 50, l: 60 },
      yaxis: { title: "Affordability Ratio" },
      xaxis: { title: "Date" }
    },
    { responsive: true }
  );
}


let currentSortKey = null;
let sortAscending = true;

function renderTable() {
  const tbody = document.querySelector("#state-table tbody");
  tbody.innerHTML = "";

  let data = [...dashboardData.table_data];

  if (currentSortKey) {
    data.sort((a, b) => {
      if (typeof a[currentSortKey] === "number") {
        return sortAscending
          ? a[currentSortKey] - b[currentSortKey]
          : b[currentSortKey] - a[currentSortKey];
      } else {
        return sortAscending
          ? a[currentSortKey].localeCompare(b[currentSortKey])
          : b[currentSortKey].localeCompare(a[currentSortKey]);
      }
    });
  }

  data.forEach(row => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${row.state}</td>
      <td>${formatCurrency(row.current_price)}</td>
      <td>${formatCurrency(row.forecast_price)}</td>
      <td>${row.current_ratio.toFixed(2)}</td>
      <td>${row.forecast_ratio.toFixed(2)}</td>
      <td>${row.change > 0 ? "▲" : "▼"} ${Math.abs(row.change).toFixed(2)}</td>
      <td><span class="tag ${row.label.toLowerCase()}">${row.label}</span></td>
    `;

    tbody.appendChild(tr);
  });
}

function renderInsights() {
  const data = dashboardData.table_data;

  const sorted = [...data].sort((a, b) => b.current_ratio - a.current_ratio);

  const top5 = sorted.slice(0, 5);
  const bottom5 = [...sorted].reverse().slice(0, 5);

  const improving = data
    .filter(d => d.change > 0)
    .sort((a, b) => b.change - a.change)
    .slice(0, 3);

  const worsening = data
    .filter(d => d.change < 0)
    .sort((a, b) => a.change - b.change)
    .slice(0, 3);

  document.getElementById("top-affordable").innerHTML =
    top5.map(d => `<li>${d.state} (${d.current_ratio.toFixed(2)})</li>`).join("");

  document.getElementById("least-affordable").innerHTML =
    bottom5.map(d => `<li>${d.state} (${d.current_ratio.toFixed(2)})</li>`).join("");

  document.getElementById("trend-summary").innerHTML = `
    <strong style="color:#2563eb;">Improving:</strong> ${improving.map(d => d.state).join(", ")}<br><br>
    <strong style="color:#dc2626;">Worsening:</strong> ${worsening.map(d => d.state).join(", ")}
  `;
}





function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value);
}

