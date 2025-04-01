# --------------------------------------------------
# Assignment: Assignment 7
# File:    scraper.py
# Author:  Zaki Rangwala (210546860)
# Version: 2025-04-01
# --------------------------------------------------

# import libraries
import pandas as pd
import pycountry
import logging
import re

# Configure logging when run directly
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scraper.log'),
            logging.StreamHandler()
        ]
    )

# get the world cup data


def get_world_cup_data():
    # Get logger for this file
    logger = logging.getLogger(__name__)

    ########################################################
    # Phase 1 : Load and clean the data
    ########################################################

    # load Wikipedia page
    url = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"
    tables = pd.read_html(url)

    logger.info("Loaded Wikipedia page")

    # find the correct FIFA World Cup finals table
    finals_df = None
    for table in tables:
        if 'Winners' in table.columns and 'Runners-up' in table.columns:
            finals_df = table
            break

    if finals_df is None:
        raise Exception(
            "Could not find the correct FIFA World Cup finals table.")

    logger.info("Found 'FIFA World Cup finals' table")

    # standardize column names (some tables might have footnotes or merged columns)
    finals_df.columns = [col if not isinstance(
        col, tuple) else col[1] for col in finals_df.columns]
    finals_df = finals_df.rename(columns={
        'Year': 'Year',
        'Winners': 'Winners',
        'Runners-up': 'Runners-up',
        'Score': 'Score',
        'Venue': 'Venue',
        'Attendance': 'Attendance'
    })

    # clean data
    finals_df = finals_df.dropna(subset=['Year', 'Winners', 'Runners-up'])
    finals_df['Year'] = finals_df['Year'].astype(
        str).str.extract(r'(\d{4})')

    # treat 'West Germany' and 'Germany' as the same
    finals_df['Winners'] = finals_df['Winners'].replace(
        'West Germany', 'Germany')
    finals_df['Runners-up'] = finals_df['Runners-up'].replace(
        'West Germany', 'Germany')

    logger.info("Cleaned Finals table")

    # find "Results by nation" table: look for one with 'Team', 'Winners', etc.
    nation_df = None
    for table in tables:
        if 'Team' in table.columns and 'Winners' in table.columns:
            nation_df = table
            break

    if nation_df is None:
        raise Exception("Could not find the 'Results by nation' table.")

    logger.info("Found 'Results by nation' table")

    # Clean and rename columns
    nation_df = nation_df.rename(columns={
        'Team': 'Country',
        'Winners': 'Wins',
        'Runners-up': 'RunnerUps',
        'Total finals': 'TotalFinals',
        'Years won': 'YearsWon',
        'Years runners-up': 'YearsRunnerUp'
    })

    logger.info("Cleaned Results by Nation table")

    # Fix country name issues
    nation_df['Country'] = nation_df['Country'].replace({
        'West Germany': 'Germany',
        'Soviet Union': 'Russia',
        'Czechoslovakia': 'Czech Republic',
        'Yugoslavia': 'Serbia',
        'England': 'United Kingdom'
    })

    logger.info("Fixed country name issues for ISO Alpha-3 codes")

    # add ISO Alpha-3 codes
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

    logger.info("Added ISO codes")

    # Fill NaNs for countries with no wins or runner-ups
    nation_df[['Wins', 'RunnerUps', 'TotalFinals']] = nation_df[[
        'Wins', 'RunnerUps', 'TotalFinals']].fillna(0).astype(int)
    nation_df[['YearsWon', 'YearsRunnerUp']] = nation_df[[
        'YearsWon', 'YearsRunnerUp']].fillna('—')

    logger.info("Filled NaNs for countries with no wins or runner-ups")

    # Set display options for better readability
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_rows', 10)
    pd.set_option('display.max_colwidth', None)

    # # log the dataframes
    # logging.info("Show DataFrames")
    # logging.info("\nNation DF:\n%s", nation_df.to_string())
    # logging.info("\nFinals DF:\n%s", finals_df.to_string())

    ########################################################
    # Phase 2 : Preprocess the data
    ########################################################

    # replace '—' with None
    logger.info("Cleaning YearsWon and YearsRunnerUp columns...")
    nation_df['YearsWon'] = nation_df['YearsWon'].replace('—', None)
    nation_df['YearsRunnerUp'] = nation_df['YearsRunnerUp'].replace('—', None)

    # convert to lists of ints
    def parse_years(val):
        if pd.isna(val):
            return []
        return [int(y.strip()) for y in val.split(',') if y.strip().isdigit()]

    # apply the parse_years function to the YearsWon and YearsRunnerUp columns
    nation_df['YearsWon'] = nation_df['YearsWon'].apply(parse_years)
    nation_df['YearsRunnerUp'] = nation_df['YearsRunnerUp'].apply(parse_years)

    # clean 'Score' column in finals_df and create 'Notes'
    logger.info("Normalizing Score and extracting match notes...")

    def clean_score(score):
        if pd.isna(score):
            return None, None

        notes = []
        # extract extra time or penalties
        if '(a.e.t.)' in score:
            notes.append('extra time')
            score = score.replace('(a.e.t.)', '')

        # extract penalty scores using regex
        pen_match = re.search(r'\((\d+[–-]\d+)\s*pen\.\)', score)
        if pen_match:
            notes.append(f"({pen_match.group(1)} pen.)")
            score = re.sub(r'\(\d+[–-]\d+\s*pen\.\)', '', score)

        # remove any references like [n 3]
        score = re.sub(r'\[.*?\]', '', score)

        # if no notes were found, set to None instead of empty list
        return score.strip(), notes if notes else None

    finals_df[['CleanedScore', 'Notes']] = finals_df['Score'].apply(
        lambda x: pd.Series(clean_score(x)))

    # drop 'Ref.' column if it exists
    if 'Ref.' in finals_df.columns:
        logger.info("Dropping 'Ref.' column...")
        finals_df.drop(columns=['Ref.'], inplace=True)

    # log the dataframes
    logger.info("\nFinals DF:\n%s", finals_df.to_string())
    logger.info("\nNation DF:\n%s", nation_df.to_string())

    # write the dataframes to csv
    finals_df.to_csv('data/world_cup_finals.csv', index=False)
    nation_df.to_csv('data/world_country_stats.csv', index=False)
    logger.info("Dataframes written to csv")

    # Return the processed DataFrames
    return finals_df, nation_df


if __name__ == '__main__':
    get_world_cup_data()
