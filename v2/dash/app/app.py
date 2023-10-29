
# Importing the necessary libraries for the sample Dash app
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import psycopg2

# Sample code to initialize the Dash app
app = Dash(__name__)

db_params = {
        'dbname': 'localdev',
        'user': 'shaun',
        'password': '123546',
        'host': 'localhost',
        'port': 5433
    }

# Sample code to connect to a PostgreSQL database
def fetch_data():
    conn = psycopg2.connect(**db_params)
    sql_query = "SELECT * FROM stock_data LIMIT 100;"
    df = pd.read_sql(sql_query, conn)
    conn.close()
    return df

# Sample Dash layout
app.layout = html.Div([
    html.H1("Stock Data Visualization"),
    dcc.Dropdown(id='stock-selector', options=[{'label': 'AAPL', 'value': 'AAPL'}, {'label': 'GOOGL', 'value': 'GOOGL'}], value='AAPL'),
    dcc.Graph(id='price-chart')
])

# Sample Dash callback to update the chart based on stock selection
@app.callback(
    Output('price-chart', 'figure'),
    [Input('stock-selector', 'value')]
)
def update_chart(selected_stock):
    filtered_df = df[df['stock'] == selected_stock]
    fig = px.line(filtered_df, x='date', y='price', title=f'Historical Prices of {selected_stock}')
    return fig

# Uncomment the line below in your actual code to run the app
# if __name__ == '__main__':
#    app.run_server(debug=True)
