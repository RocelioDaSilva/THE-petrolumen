from __future__ import annotations

from typing import TYPE_CHECKING

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

if TYPE_CHECKING:
    from ..engines.visualization.advanced_visualization import AdvancedVisualization


def create_interactive_dashboard(visualization: AdvancedVisualization) -> None:
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("Reservoir Analytics Dashboard"),
        html.Div([
            html.Div([
                html.H3("Production Analysis"),
                dcc.Graph(id="production-graph")
            ], className="six columns"),
            html.Div([
                html.H3("Well Analysis"),
                dcc.Graph(id="well-graph")
            ], className="six columns")
        ], className="row"),
        html.Div([
            html.H3("Filters"),
            dcc.Dropdown(
                id="well-selector",
                options=[
                    {"label": f"Well {well}", "value": well}
                    for well in visualization.data["production"]["well"].unique()
                ],
                value=visualization.data["production"]["well"].iloc[0],
                multi=True
            )
        ])
    ])

    @app.callback(
        Output("production-graph", "figure"),
        Input("well-selector", "value")
    )
    def update_production_graph(selected_wells):
        production = visualization.data["production"]
        filtered = production[production["well"].isin(selected_wells)]
        figure = go.Figure()
        for well in selected_wells:
            well_data = filtered[filtered["well"] == well]
            figure.add_trace(
                go.Scatter(
                    x=well_data["date"],
                    y=well_data["oil_rate"],
                    name=f"Well {well}"
                )
            )
        return figure

    visualization.dashboards["interactive"] = app
