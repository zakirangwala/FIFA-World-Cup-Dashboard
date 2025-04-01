from scraper import get_world_cup_data
import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import logging

# Configure logging before importing scraper
logging.basicConfig(
    level=logging.WARNING,  # Set default level to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# Suppress scraper logs
logging.getLogger('scraper').setLevel(logging.WARNING)

# Now import scraper after logging is configured

# Set specific log levels for different modules
logging.getLogger('app').setLevel(logging.INFO)  # Our app logs

# Get logger for this file only
logger = logging.getLogger('app')

# Initialize the Dash app
app = dash.Dash(__name__)

# Load the data
try:
    logger.info("Loading World Cup data...")
    finals_df, nation_df = get_world_cup_data()
    logger.info(
        f"Successfully loaded data. Finals shape: {finals_df.shape}, Nations shape: {nation_df.shape}")
except Exception as e:
    logger.error(f"Error loading data: {str(e)}")
    raise

# Define the layout
app.layout = html.Div([
    html.H1('FIFA World Cup Dashboard',
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),

    # Choropleth Map
    html.Div([
        dcc.Graph(id='world-map')
    ], style={'width': '100%', 'height': '60vh'}),

    # Controls
    html.Div([
        html.Div([
            html.Label('Select Country:'),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': country, 'value': country}
                         for country in nation_df['Country'].unique()],
                value=None
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),

        html.Div([
            html.Label('Select Year:'),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': year, 'value': year}
                         for year in sorted(finals_df['Year'].unique())],
                value=None
            )
        ], style={'width': '30%', 'display': 'inline-block'})
    ], style={'marginTop': '20px', 'marginBottom': '20px'}),

    # Statistics Panel
    html.Div([
        html.H3('Statistics', style={'color': '#2c3e50'}),
        html.Div(id='stats-panel')
    ], style={'marginTop': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
])


@app.callback(
    dash.Output('world-map', 'figure'),
    dash.Input('country-dropdown', 'value'),
    dash.Input('year-dropdown', 'value')
)
def update_map(selected_country, selected_year):
    try:
        logger.info(
            f"Updating map with country: {selected_country}, year: {selected_year}")

        # Create choropleth data
        map_data = nation_df.copy()

        # Filter data based on selection
        if selected_country:
            map_data = map_data[map_data['Country'] == selected_country]
        if selected_year:
            year_data = finals_df[finals_df['Year'] == selected_year]
            map_data = map_data[map_data['Country'].isin(
                [year_data['Winner'].iloc[0], year_data['Runner-up'].iloc[0]])]

        fig = px.choropleth(
            map_data,
            locations='Country',
            locationmode='country names',
            color='Wins',
            color_continuous_scale='Viridis',
            scope='world'
        )

        fig.update_layout(
            title='World Cup Winners by Country',
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular'
            )
        )

        logger.info("Map updated successfully")
        return fig

    except Exception as e:
        logger.error(f"Error updating map: {str(e)}")
        # Return a basic map in case of error
        fig = px.choropleth(
            locations=['BR'],
            locationmode='country names',
            color=[1],
            color_continuous_scale='Viridis',
            scope='world'
        )
        return fig


if __name__ == '__main__':
    logger.info("Starting the Dash application...")
    app.run_server(debug=True)
