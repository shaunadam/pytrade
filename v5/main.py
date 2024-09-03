from src.data.fetcher import DataFetcher
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE


def main():
    fetcher = DataFetcher(DB_PATH)
    fetcher.update_all_stocks(TSX_SYMBOLS, START_DATE, END_DATE)


if __name__ == "__main__":
    main()
