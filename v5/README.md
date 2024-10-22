# TSX Swing Trading Dashboard

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)

An advanced algorithmic trading platform focused on swing trading strategies for the Toronto Stock Exchange (TSX). This platform aims to streamline the stock screening process, backtest custom strategies, and provide an interactive dashboard for analysis and visualization.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Initialization](#database-initialization)
- [Usage](#usage)
  - [Data Update](#data-update)
  - [Indicator Recalculation](#indicator-recalculation)
  - [Running the Dashboard](#running-the-dashboard)
  - [Using Screeners](#using-screeners)
- [Project Structure](#project-structure)
- [To-Do List](#to-do-list)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Data Fetching and Management**
  - Fetches daily and weekly stock data from Yahoo Finance using `yfinance`.
  - Stores data in a SQLite database for efficient retrieval and processing.
- **Technical Indicators**
  - Calculates essential technical indicators like SMA, EMA, RSI, MACD, and Bollinger Bands.
  - Supports both daily and weekly time frames.
- **Custom Screeners**
  - Define custom stock screeners using YAML configuration files.
  - Includes example screeners like Golden Cross, RSI Oversold Rebound, Bollinger Bands Breakout, and MACD Bullish Crossover.
- **Interactive Dashboard**
  - Built with Dash and Plotly for real-time data visualization.
  - Features tabs for Technical Analysis, Stock Screening, Backtesting (under development), and Utilities.
  - Provides interactive charts for price, volume, MACD, and RSI.
- **Utilities**
  - Update stock data and indicators directly from the dashboard.
  - Override date ranges for data fetching and indicator calculations.
- **Modular Architecture**
  - Organized codebase with clear separation of concerns.
  - Easy to extend and customize with additional features or indicators.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/tsx-swing-trading-dashboard.git
   cd tsx-swing-trading-dashboard
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### Database Initialization

Initialize the SQLite database by running:

```bash
python src/database/init_db.py
```

This will create a `stocks.db` file in the `data` directory.

## Usage

### Data Update

To fetch the latest stock data and update the database:

```bash
python main.py --update
```

### Indicator Recalculation

To recalculate technical indicators:

```bash
python main.py --recalculate
```

You can specify the time frame (daily or weekly):

```bash
python main.py --recalculate --time_frame weekly
```

### Running the Dashboard

Launch the interactive dashboard:

```bash
python main.py --dashboard
```

Open your web browser and navigate to `http://127.0.0.1:8050/` to access the dashboard.

### Using Screeners

Run a specific screener:

```bash
python main.py --screener bollinger_breakout
```

## Project Structure

```
├── config.py
├── main.py
├── requirements.txt
├── src
│   ├── analysis
│   │   ├── bollinger_breakout.yaml
│   │   ├── gold_cross.yaml
│   │   ├── indicators.py
│   │   ├── macd_bullish_cross.yaml
│   │   ├── rsi_oversold_rebound.yaml
│   │   └── screener.py
│   ├── data
│   │   └── fetcher.py
│   ├── database
│   │   └── init_db.py
│   ├── visualization
│   │   ├── assets
│   │   │   └── custom.css
│   │   ├── callbacks
│   │   │   ├── analysis_callbacks.py
│   │   │   ├── backtesting_callbacks.py
│   │   │   ├── screening_callbacks.py
│   │   │   └── utilities_callbacks.py
│   │   ├── components
│   │   │   ├── analysis_tab.py
│   │   │   ├── backtesting_tab.py
│   │   │   ├── screening_tab.py
│   │   │   └── utilities_tab.py
│   │   └── dashboard.py
│   └── todo.md
```

- **config.py**: Configuration settings like database path, stock symbols, and date ranges.
- **main.py**: Entry point for running data updates, indicator recalculations, dashboard, and screeners.
- **requirements.txt**: Python dependencies.
- **src/analysis**: Contains screener configurations and indicator calculations.
- **src/data**: Data fetching and processing logic.
- **src/database**: Database models and initialization.
- **src/visualization**: Dashboard components, callbacks, and assets.
- **src/todo.md**: Project to-do list and notes.

## To-Do List

- **Weekly Data Handling**
  - Optimize weekly data aggregation to respect selected symbols and date ranges.
- **Multi-Time Frame Support**
  - Enhance strategies to support multiple time frames seamlessly.
- **Backtesting Engine**
  - Develop a config-based backtesting system with order management, position sizing, and performance metrics.
- **Unit Testing**
  - Write comprehensive unit tests for critical components.

For a detailed list, refer to [todo.md](src/todo.md).

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

   Click on the "Fork" button at the top right of the repository page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/yourusername/tsx-swing-trading-dashboard.git
   ```

3. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes and Commit**

   ```bash
   git add .
   git commit -m "Add your message here"
   ```

5. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

   Navigate to the original repository and click on "New Pull Request".

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Author**: Your Name
- **Email**: your.email@example.com
- **GitHub**: [yourusername](https://github.com/yourusername)

Feel free to reach out for any questions or collaboration opportunities!

---

*Happy Trading!*
