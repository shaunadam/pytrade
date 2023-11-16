
# Importing the necessary libraries for the sample Dash app
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import datetime, timedelta
from typing import List
import dash_bootstrap_components as dbc

import data.fetch as fetch

db_params = {
    'dbname': 'localdev',
    'user': 'shaun',
    'password': '123546',
    'host': 'my_postgres_container',
    'port': 5432
}
def get_multi_ticker_data_pg(conn, tickers: List[str], date) -> pd.DataFrame:
    #date_from = datetime.now() - timedelta(days=days)
    query = """
    SELECT * FROM stock_data
    WHERE "ticker" = ANY(%s) AND "date" >= %s
    order by "ticker","date"
    """
    df = pd.read_sql_query(query, conn, params=(tickers, date))
    return df

def ticker_list():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT \"ticker\" FROM stock_data")
    tickers = [row[0] for row in cur.fetchall()]
    tick_list = []
    for x in tickers:
        tick_list.append({'value':x,'label':x})
    conn.close()
    return tick_list


date_from = datetime.now() - timedelta(days=90)

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.Div("Stock Data Visualization"))),
    dbc.Row([
        dbc.Col(html.Button('Refresh Data',id='refreshData',n_clicks=0),width=3),
        dbc.Col(html.Button('Calculate Indicators',id='refreshInd',n_clicks=0),width=3)]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='stock-selector', options=ticker_list(), value='SU.TO', multi=True), width=6),
        dbc.Col(dcc.DatePickerSingle(id='dStart',date=date_from), width=6)
    ]),
    dbc.Row(dbc.Col(dcc.Graph(id='price-chart'))),
    dbc.Row(dbc.Col(html.Div(id='stat')))
], fluid=True)


@app.callback(
    Output('price-chart', 'figure'),
    [Input('stock-selector', 'value')
    ,Input('dStart','date')
    ]
)
def update_chart(selected_stock,date):
    df = get_multi_ticker_data_pg(psycopg2.connect(**db_params),[selected_stock],date)
    fig = px.line(df, x='date', y='adj close', title=f'Historical Prices of {selected_stock}', color='ticker')
    return fig

@app.callback(
    Output('stat','children'),
    Input('refreshData','n_clicks'),
    prevent_initial_call=True
)
def update_data(clicks):
    fetch.main()
    return 'data retrieved.'


if __name__ == '__main__':
   app.run_server(debug=True, host='0.0.0.0')
