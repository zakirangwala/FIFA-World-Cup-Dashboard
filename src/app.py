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
        html.Div(id='stats-panel',
                 style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'})
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
                [year_data['Winners'].iloc[0], year_data['Runners-up'].iloc[0]])]

        # Create hover text with both wins and runner-up appearances
        map_data['hover_text'] = map_data.apply(
            lambda row: f"Country: {row['Country']}<br>" +
            f"World Cup Wins: {row['Wins']}<br>" +
            f"Runner-up Appearances: {row['RunnerUps']}<br>" +
            f"Total Finals: {row['TotalFinals']}",
            axis=1
        )

        fig = px.choropleth(
            map_data,
            locations='Country',
            locationmode='country names',
            color='TotalFinals',
            color_continuous_scale='Viridis',
            scope='world',
            hover_name='Country',
            custom_data=['Wins', 'RunnerUps', 'TotalFinals']
        )

        fig.update_layout(
            title='World Cup Final Appearances by Country',
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular'
            ),
            coloraxis_colorbar=dict(
                title='Total Finals Appearances',
                ticksuffix=''
            )
        )

        # Update hover template to show country first and avoid duplicates
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br><br>" +
            "World Cup Wins: %{customdata[0]}<br>" +
            "Runner-up Appearances: %{customdata[1]}<br>" +
            "Total Finals: %{customdata[2]}" +
            "<extra></extra>"
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


@app.callback(
    dash.Output('stats-panel', 'children'),
    dash.Input('country-dropdown', 'value'),
    dash.Input('year-dropdown', 'value')
)
def update_stats(selected_country, selected_year):
    try:
        if not selected_country and not selected_year:
            return html.Div("Select a country or year to view statistics")

        stats_components = []

        if selected_country:
            country_stats = nation_df[nation_df['Country']
                                      == selected_country].iloc[0]

            # Create country statistics cards
            stats_components.extend([
                html.Div([
                    html.H4(f"{selected_country} Statistics",
                            style={'color': '#2c3e50'}),
                    html.Div([
                        html.P(f"Total World Cup Wins: {country_stats['Wins']}",
                               style={'fontSize': '1.2em', 'color': '#27ae60'}),
                        html.P(f"Runner-up Appearances: {country_stats['RunnerUps']}",
                               style={'fontSize': '1.2em', 'color': '#e74c3c'}),
                        html.P(f"Total Finals Appearances: {country_stats['TotalFinals']}",
                               style={'fontSize': '1.2em', 'color': '#3498db'}),
                        html.P("Years Won: " + ", ".join(map(str, country_stats['YearsWon'])) if country_stats['YearsWon'] else "No wins yet",
                               style={'fontSize': '1.2em'}),
                        html.P("Runner-up Years: " + ", ".join(map(str, country_stats['YearsRunnerUp'])) if country_stats['YearsRunnerUp'] else "No runner-up appearances",
                               style={'fontSize': '1.2em'})
                    ])
                ], style={'flex': '1', 'minWidth': '300px', 'padding': '15px',
                          'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            ])

        if selected_year:
            year_data = finals_df[finals_df['Year'] == selected_year].iloc[0]

            # Create year statistics card
            stats_components.append(
                html.Div([
                    html.H4(f"{selected_year} World Cup Final",
                            style={'color': '#2c3e50'}),
                    html.Div([
                        html.P(f"Winner: {year_data['Winners']}",
                               style={'fontSize': '1.2em', 'color': '#27ae60'}),
                        html.P(f"Runner-up: {year_data['Runners-up']}",
                               style={'fontSize': '1.2em', 'color': '#e74c3c'}),
                        html.P(f"Score: {year_data['CleanedScore']}",
                               style={'fontSize': '1.2em', 'fontWeight': 'bold'}),
                        html.P(f"Venue: {year_data['Venue']}",
                               style={'fontSize': '1.2em'}),
                        html.P(f"Location: {year_data['Location']}",
                               style={'fontSize': '1.2em'}),
                        html.P(f"Attendance: {int(year_data['Attendance']):,}",
                               style={'fontSize': '1.2em'}),
                        html.P(f"Notes: {year_data['Notes'] if year_data['Notes'] else 'None'}",
                               style={'fontSize': '1.2em'})
                    ])
                ], style={'flex': '1', 'minWidth': '300px', 'padding': '15px',
                          'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            )

        return stats_components

    except Exception as e:
        logger.error(f"Error updating statistics: {str(e)}")
        return html.Div("Error loading statistics")


if __name__ == '__main__':
    logger.info("Starting the Dash application...")
    app.run_server(debug=True)
