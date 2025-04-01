# FIFA World Cup Dashboard

An interactive dashboard visualizing FIFA World Cup winners and runner-ups from 1930 to 2022. Built with Dash, Plotly, and Python.

## Live Demo

The dashboard is deployed and accessible at: [FIFA World Cup Dashboard](https://fifa-world-cup-dashboard-production.up.railway.app/)

## Features

- **Interactive World Map**: Choropleth visualization showing World Cup final appearances
- **Country Statistics**: View detailed statistics for each country including:
  - Total World Cup wins
  - Runner-up appearances
  - Years won
  - Total finals appearances
- **Year-specific Details**: For each World Cup year, view:
  - Winner and runner-up
  - Match score
  - Venue and attendance
  - Special notes (extra time, penalties)

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the dashboard:

```bash
python src/app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:8050/
```

3. Interact with the dashboard:
   - Select countries from the dropdown to view their World Cup history
   - Choose specific years to see final match details
   - Hover over countries on the map for quick statistics

## Data Source

Data is scraped from [FIFA World Cup Finals Wikipedia page](https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals) using BeautifulSoup4.

## Project Structure

```
├── src/
│   ├── app.py          # Main dashboard application
│   ├── scraper.py      # Wikipedia data scraper
│   └── logs/           # Application logs
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Technologies Used

- Dash
- Plotly
- Pandas
- NumPy
- BeautifulSoup4
- Requests
