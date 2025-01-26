import os
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import plotly.graph_objects as go
from datetime import datetime


def generate_plotly_chart(stock_data, symbol):
    """
    stock_data: DataFrame with columns [date, open, high, low, close, volume].
    Returns an HTML string for a Plotly candlestick chart.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=stock_data["date"],
            open=stock_data["open"],
            high=stock_data["high"],
            low=stock_data["low"],
            close=stock_data["close"],
            name=symbol,
        )
    )
    fig.update_layout(
        title=f"{symbol} Price Chart", xaxis_title="Date", yaxis_title="Price"
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_html_report(detailed_results, output_dir="reports"):
    """
    detailed_results: dictionary like:
        {
            'RSIOversoldScreener': [
                {
                    'symbol': 'ABC.TO',
                    'latest_price': 12.34,
                    'rsi': 28.5,
                    'macd': 0.12,
                    'sma50': ...,
                    'sma200': ...,
                    'data': <DataFrame with full price history>
                },
                ...
            ],
            'MACDBullishCrossScreener': [...],
            ...
        }
    """
    os.makedirs(output_dir, exist_ok=True)
    env = Environment(loader=FileSystemLoader("."))
    template = env.from_string(HTML_TEMPLATE)

    # Build plotly charts for each screener + symbol
    plots = {}
    for screener, stocks in detailed_results.items():
        for stock in stocks:
            symbol = stock["symbol"]
            df_for_plot = stock["data"]
            # Convert your stock data DataFrame into a Plotly candlestick chart
            plot_html = generate_plotly_chart(df_for_plot, symbol)
            # Store in a dict keyed by screener_symbol
            plots[f"{screener}_{symbol}"] = plot_html

    # Render final HTML from template
    report_html = template.render(
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        detailed_results=detailed_results,
        plots=plots,
    )

    # Write out the .html file
    report_path = os.path.join(
        output_dir, f"screener_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    with open(report_path, "w") as file:
        file.write(report_html)

    print(f"Report generated at: {report_path}")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Stock Screener Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #f4f4f4; }
    </style>
</head>
<body>
<h1>Stock Screener Report</h1>
<p>Generated on: {{ generation_date }}</p>

{% for screener, stocks in detailed_results.items() %}
    <h2>{{ screener }} - Matching Stocks</h2>
    <table>
        <tr>
            <th>Symbol</th>
            <th>Latest Price</th>
            <th>RSI</th>
            <th>MACD</th>
            <th>SMA50</th>
            <th>SMA200</th>
        </tr>
        {% for stock in stocks %}
        <tr>
            <td>{{ stock.symbol }}</td>
            <td>{{ stock.latest_price }}</td>
            <td>{{ stock.rsi }}</td>
            <td>{{ stock.macd }}</td>
            <td>{{ stock.sma50 }}</td>
            <td>{{ stock.sma200 }}</td>
        </tr>
        {% endfor %}
    </table>

    <!-- Insert the Plotly chart for each symbol -->
    {% for stock in stocks %}
    <div>
        {{ plots[screener + '_' + stock.symbol] | safe }}
    </div>
    {% endfor %}
{% endfor %}

<footer>
    <p>Note: This report is for informational purposes only and not financial advice.</p>
</footer>
</body>
</html>
"""
