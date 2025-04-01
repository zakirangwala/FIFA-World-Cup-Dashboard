# --------------------------------------------------
# Assignment: Assignment 7
# File:    app.py
# Author:  Zaki Rangwala (210546860)
# Version: 2025-04-01
# --------------------------------------------------

# import libraries
from scraper import get_world_cup_data
import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import logging
import os

# configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# suppress scraper logs
logging.getLogger('scraper').setLevel(logging.WARNING)
logging.getLogger('app').setLevel(logging.INFO)
logger = logging.getLogger('app')

# initialize the dash app
app = dash.Dash(__name__)
server = app.server

# add css styles
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>FIFA World Cup Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #2c3e50;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .stats-card {
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 20px;
                margin: 10px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# load the data
try:
    logger.info("Loading World Cup data...")
    finals_df, nation_df = get_world_cup_data()
    logger.info(
        f"Successfully loaded data. Finals shape: {finals_df.shape}, Nations shape: {nation_df.shape}")
except Exception as e:
    logger.error(f"Error loading data: {str(e)}")
    raise

# define the layout
app.layout = html.Div([
    html.H1('FIFA World Cup Dashboard',
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),

    # choropleth map
    html.Div([
        dcc.Graph(id='world-map')
    ], style={'width': '100%', 'height': '60vh'}),

    # controls
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

    # statistics panel
    html.Div([
        html.H3('Statistics', style={'color': '#2c3e50'}),
        html.Div(id='stats-panel',
                 style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'})
    ], style={'marginTop': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),

    # historical summary
    html.Div([
        html.H3('Historical Summary', style={
                'color': '#2c3e50', 'marginBottom': '20px'}),
        html.Div([
            html.Div([
                html.H4('Most Successful Countries',
                        style={'color': '#2c3e50'}),
                html.Div(id='top-countries')
            ], style={'flex': '1', 'minWidth': '300px', 'padding': '15px',
                      'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '20px'}),

            html.Div([
                html.H4('Tournament Facts', style={'color': '#2c3e50'}),
                html.Div(id='tournament-facts')
            ], style={'flex': '1', 'minWidth': '300px', 'padding': '15px',
                      'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'})
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

        # create choropleth data
        map_data = nation_df.copy()

        # filter data based on selection
        if selected_country:
            map_data = map_data[map_data['Country'] == selected_country]
        if selected_year:
            year_data = finals_df[finals_df['Year'] == selected_year]
            map_data = map_data[map_data['Country'].isin(
                [year_data['Winners'].iloc[0], year_data['Runners-up'].iloc[0]])]

        # create hover text with both wins and runner-up appearances
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
            color_continuous_scale=[
                [0, 'lightgrey'],     # For countries with no appearances
                [0.2, '#ffffcc'],     # Light yellow for few appearances
                [0.4, '#a1dab4'],     # Light green
                [0.6, '#41b6c4'],     # Turquoise
                [0.8, '#2c7fb8'],     # Blue
                [1.0, '#253494']      # Dark blue for most appearances
            ],
            scope='world',
            hover_name='Country',
            custom_data=['Wins', 'RunnerUps', 'TotalFinals']
        )

        fig.update_layout(
            title={
                'text': 'FIFA World Cup Final Appearances by Country (1930-2022)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24}
            },
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular',
                showland=True,
                landcolor='lightgray',
                showocean=True,
                oceancolor='aliceblue'
            ),
            coloraxis_colorbar=dict(
                title='Finals Appearances',
                ticksuffix='',
                len=0.75,
                title_font={'size': 14},
                tickfont={'size': 12}
            ),
            margin=dict(l=0, r=0, t=50, b=0)
        )

        # update hover template to show country first and avoid duplicates
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
        # return a basic map in case of error
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

            # create country statistics cards
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

            # create year statistics card
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


@app.callback(
    [dash.Output('top-countries', 'children'),
     dash.Output('tournament-facts', 'children')],
    # Dummy input to initialize the callback
    [dash.Input('country-dropdown', 'value')]
)
def update_historical_summary(dummy):
    try:
        # top countries by wins
        top_winners = nation_df.nlargest(
            5, 'Wins')[['Country', 'Wins', 'RunnerUps']]

        # calculate interesting statistics
        total_finals = len(finals_df)
        total_countries = len(nation_df)
        avg_goals = finals_df['CleanedScore'].apply(
            lambda x: sum(map(int, x.split('–')))).mean()
        extra_time_matches = finals_df['Notes'].str.contains(
            'extra time', na=False).sum()
        penalty_matches = finals_df['Notes'].str.contains(
            'pen.', na=False).sum()

        # create top countries table
        top_countries_content = [
            html.Table([
                html.Thead(
                    html.Tr([
                        html.Th('Country'),
                        html.Th('Wins'),
                        html.Th('Runner-ups')
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(row['Country']),
                        html.Td(row['Wins']),
                        html.Td(row['RunnerUps'])
                    ]) for _, row in top_winners.iterrows()
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse'})
        ]

        # create tournament facts
        tournament_facts_content = [
            html.P(f"Total World Cups: {total_finals}"),
            html.P(f"Participating Countries in Finals: {total_countries}"),
            html.P(f"Average Goals in Finals: {avg_goals:.2f}"),
            html.P(f"Finals with Extra Time: {extra_time_matches}"),
            html.P(f"Finals Decided by Penalties: {penalty_matches}")
        ]

        return top_countries_content, tournament_facts_content

    except Exception as e:
        logger.error(f"Error updating historical summary: {str(e)}")
        return html.Div("Error loading data"), html.Div("Error loading data")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    logger.info("Starting the Dash application...")
    app.run_server(debug=False, host='0.0.0.0', port=port)
