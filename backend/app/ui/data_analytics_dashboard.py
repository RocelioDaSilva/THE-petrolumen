from __future__ import annotations

from typing import TYPE_CHECKING

from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px

if TYPE_CHECKING:
    from ..engines.data_analytics import DataAnalytics


def create_dashboard(analytics: DataAnalytics) -> None:
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Monitoramento de Reservatório"),
                html.Hr()
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.H3("Produção"),
                dcc.Graph(id='production-plot')
            ], width=6),
            dbc.Col([
                html.H3("Pressão"),
                dcc.Graph(id='pressure-plot')
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                html.H3("Padrões de Produção"),
                dcc.Graph(id='pattern-plot')
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.H3("Controles"),
                dbc.Select(
                    id='well-selector',
                    options=[
                        {'label': well, 'value': well}
                        for well in analytics.production_data['well_name'].unique()
                    ],
                    value=analytics.production_data['well_name'].unique()[0]
                ),
                dbc.Select(
                    id='time-range',
                    options=[
                        {'label': '1 mês', 'value': 30},
                        {'label': '3 meses', 'value': 90},
                        {'label': '6 meses', 'value': 180},
                        {'label': '1 ano', 'value': 365}
                    ],
                    value=90
                )
            ], width=3)
        ])
    ])

    @app.callback(
        [Output('production-plot', 'figure'),
         Output('pressure-plot', 'figure'),
         Output('pattern-plot', 'figure')],
        [Input('well-selector', 'value'),
         Input('time-range', 'value')]
    )
    def update_plots(well_name, time_range):
        well_data = analytics.production_data[
            (analytics.production_data['well_name'] == well_name) &
            (analytics.production_data['time'] <= time_range)
        ]
        production_fig = px.line(
            well_data,
            x='time',
            y='rate',
            title=f'Produção - {well_name}'
        )
        pressure_fig = px.line(
            well_data,
            x='time',
            y='pressure',
            title=f'Pressão - {well_name}'
        )
        pattern_fig = px.scatter(
            analytics.production_patterns['features_pca'],
            x=0,
            y=1,
            color=analytics.production_patterns['clusters'],
            title='Padrões de Produção'
        )
        return production_fig, pressure_fig, pattern_fig

    analytics.dashboard = app


def run_dashboard(
    analytics: DataAnalytics,
    debug: bool = True,
    port: int = 8050,
) -> None:
    if analytics.dashboard is None:
        raise ValueError("Dashboard não criado")
    analytics.dashboard.run_server(debug=debug, port=port)
