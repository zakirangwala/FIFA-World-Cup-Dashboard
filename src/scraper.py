import pandas as pd
import pycountry

# Load Wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"
tables = pd.read_html(url)

# Find "Results by nation" table: look for one with 'Team', 'Winners', etc.
nation_df = None
for table in tables:
    if 'Team' in table.columns and 'Winners' in table.columns:
        nation_df = table
        break

if nation_df is None:
    raise Exception("Could not find the 'Results by nation' table.")

# Clean and rename columns
nation_df = nation_df.rename(columns={
    'Team': 'Country',
    'Winners': 'Wins',
    'Runners-up': 'RunnerUps',
    'Total finals': 'TotalFinals',
    'Years won': 'YearsWon',
    'Years runners-up': 'YearsRunnerUp'
})

# Fix country name issues
nation_df['Country'] = nation_df['Country'].replace({
    'West Germany': 'Germany',
    'Soviet Union': 'Russia',
    'Czechoslovakia': 'Czech Republic',
    'Yugoslavia': 'Serbia',
    'England': 'United Kingdom'  # for ISO code
})

# Add ISO Alpha-3 codes
def get_country_code(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        overrides = {
            'Germany': 'DEU',
            'Russia': 'RUS',
            'Czech Republic': 'CZE',
            'Serbia': 'SRB',
            'United Kingdom': 'GBR'
        }
        return overrides.get(name, None)

nation_df['ISO_Code'] = nation_df['Country'].apply(get_country_code)

# Fill NaNs for countries with no wins or runner-ups
nation_df[['Wins', 'RunnerUps', 'TotalFinals']] = nation_df[['Wins', 'RunnerUps', 'TotalFinals']].fillna(0).astype(int)
nation_df[['YearsWon', 'YearsRunnerUp']] = nation_df[['YearsWon', 'YearsRunnerUp']].fillna('—')

# Save to CSV
nation_df.to_csv("world_cup_country_stats.csv", index=False)

print("✅ Enhanced country stats CSV saved as world_cup_country_stats.csv")
