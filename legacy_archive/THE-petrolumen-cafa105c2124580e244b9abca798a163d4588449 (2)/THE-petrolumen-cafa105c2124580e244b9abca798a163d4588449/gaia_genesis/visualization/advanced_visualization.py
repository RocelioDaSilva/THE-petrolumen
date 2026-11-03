import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

class AdvancedVisualization:
    """Visualização avançada de dados (estilo Spotfire)"""
    
    def __init__(self):
        self.data = {}
        self.figures = {}
        self.dashboards = {}
        
    def load_data(self, data: Dict[str, pd.DataFrame]):
        """Carrega dados para visualização"""
        self.data = data
        
    def create_production_dashboard(self):
        """Cria dashboard de produção"""
        if "production" not in self.data:
            raise ValueError("Dados de produção não encontrados")
            
        df = self.data["production"]
        
        # Gráfico de produção
        fig_production = go.Figure()
        
        for well in df["well"].unique():
            well_data = df[df["well"] == well]
            fig_production.add_trace(
                go.Scatter(x=well_data["date"],
                          y=well_data["oil_rate"],
                          name=f"Well {well}")
            )
            
        fig_production.update_layout(
            title="Production History",
            xaxis_title="Date",
            yaxis_title="Oil Rate (bbl/d)"
        )
        
        # Bubble plot de produção acumulada
        fig_bubble = px.scatter(
            df,
            x="cum_oil",
            y="cum_gas",
            size="water_cut",
            color="well",
            title="Production Cross-Plot"
        )
        
        # Mapa de calor de produtividade
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=df.pivot_table(
                values="oil_rate",
                index="well",
                columns=pd.Grouper(key="date", freq="M"),
                aggfunc="mean"
            )
        ))
        
        fig_heatmap.update_layout(
            title="Production Heatmap",
            xaxis_title="Date",
            yaxis_title="Well"
        )
        
        self.figures["production"] = {
            "history": fig_production,
            "cross_plot": fig_bubble,
            "heatmap": fig_heatmap
        }
        
    def create_well_analysis_dashboard(self):
        """Cria dashboard de análise de poços"""
        if "well_data" not in self.data:
            raise ValueError("Dados de poço não encontrados")
            
        df = self.data["well_data"]
        
        # Log plot
        fig_log = go.Figure()
        
        for log in ["GR", "RHOB", "NPHI", "RT"]:
            if log in df.columns:
                fig_log.add_trace(
                    go.Scatter(x=df[log],
                              y=df["DEPTH"],
                              name=log)
                )
                
        fig_log.update_layout(
            title="Well Logs",
            xaxis_title="Value",
            yaxis_title="Depth",
            yaxis_reversed=True
        )
        
        # Crossplot de propriedades
        fig_cross = px.scatter(
            df,
            x="RHOB",
            y="NPHI",
            color="GR",
            title="Density-Neutron Crossplot"
        )
        
        # Histograma de propriedades
        fig_hist = go.Figure()
        
        for prop in ["GR", "RHOB", "NPHI"]:
            if prop in df.columns:
                fig_hist.add_trace(
                    go.Histogram(x=df[prop],
                               name=prop,
                               opacity=0.7)
                )
                
        fig_hist.update_layout(
            title="Property Distributions",
            barmode="overlay"
        )
        
        self.figures["well_analysis"] = {
            "logs": fig_log,
            "crossplot": fig_cross,
            "histogram": fig_hist
        }
        
    def create_reservoir_dashboard(self):
        """Cria dashboard de análise de reservatório"""
        if "reservoir" not in self.data:
            raise ValueError("Dados de reservatório não encontrados")
            
        df = self.data["reservoir"]
        
        # Mapa de pressão
        fig_pressure = px.scatter_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            color="pressure",
            size="oil_rate",
            title="Reservoir Pressure Map"
        )
        
        # Gráfico de bolha de saturação
        fig_saturation = px.scatter(
            df,
            x="porosity",
            y="permeability",
            size="oil_saturation",
            color="net_pay",
            title="Reservoir Properties"
        )
        
        # Contorno de propriedades
        fig_contour = go.Figure(data=go.Contour(
            z=df.pivot_table(
                values="pressure",
                index="y_coord",
                columns="x_coord",
                aggfunc="mean"
            )
        ))
        
        self.figures["reservoir"] = {
            "pressure": fig_pressure,
            "properties": fig_saturation,
            "contour": fig_contour
        }
        
    def create_interactive_dashboard(self):
        """Cria dashboard interativo usando Dash"""
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
                        {"label": f"Well {w}", "value": w}
                        for w in self.data["production"]["well"].unique()
                    ],
                    value=self.data["production"]["well"].iloc[0],
                    multi=True
                )
            ])
        ])
        
        @app.callback(
            Output("production-graph", "figure"),
            Input("well-selector", "value")
        )
        def update_production_graph(selected_wells):
            df = self.data["production"]
            df_filtered = df[df["well"].isin(selected_wells)]
            
            fig = go.Figure()
            
            for well in selected_wells:
                well_data = df_filtered[df_filtered["well"] == well]
                fig.add_trace(
                    go.Scatter(x=well_data["date"],
                              y=well_data["oil_rate"],
                              name=f"Well {well}")
                )
                
            return fig
        
        self.dashboards["interactive"] = app
        
    def export_dashboard(self, dashboard_name: str, filename: str):
        """Exporta dashboard como HTML"""
        if dashboard_name not in self.figures:
            raise ValueError(f"Dashboard {dashboard_name} não encontrado")
            
        html_str = ""
        for fig_name, fig in self.figures[dashboard_name].items():
            html_str += fig.to_html(full_html=False)
            
        with open(filename, "w") as f:
            f.write(f"""
            <html>
                <head>
                    <title>{dashboard_name} Dashboard</title>
                </head>
                <body>
                    {html_str}
                </body>
            </html>
            """)
