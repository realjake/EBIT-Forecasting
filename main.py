import requests
from dotenv import load_dotenv
from finvizfinance.quote import Quote
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import os

class Graphing:
    def __init__(self, symbol):
        self.symbol = symbol
        self.yf_ticker = yf.Ticker(self.symbol)

    def request_fmp_api(self, version, endpoint, ticker=None, period=None):
        try:
            load_dotenv()
            api_key = os.getenv("API_KEY")
            ticker_symbol = ticker if ticker else self.symbol

            if period == 'quarterly' or period == 'annual':
                period_str = f'period={period}&' if period else ''
            else:
                period_str = ''

            url = f"https://financialmodelingprep.com/api/{version}/{endpoint}/{ticker_symbol}?{period_str}apikey={api_key}"
            print(f"Request URL: {url}")  # Print the URL to verify correctness
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Failed to fetch data: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error occurred while processing {ticker_symbol}: {e}")
            return None

if __name__ == "__main__":
    ticker = "AAPL"
    graph = Graphing(ticker)
    balance_sheet = graph.request_fmp_api('v3', 'balance-sheet-statement', ticker, 'annual')
    income_statement = graph.request_fmp_api('v3', 'income-statement', ticker, 'annual')

    if balance_sheet and income_statement:
        balance_sheet_df = pd.DataFrame(balance_sheet).set_index('date')
        income_statement_df = pd.DataFrame(income_statement).set_index('date')

        invested_capital_list = []
        roic_list = []

        for date in balance_sheet_df.index:
            total_assets = balance_sheet_df.loc[date, 'totalAssets']
            current_liabilities = balance_sheet_df.loc[date, 'totalCurrentLiabilities']
            cash_and_cash_equivalents = balance_sheet_df.loc[date, 'cashAndCashEquivalents']
            invested_capital = total_assets - current_liabilities - cash_and_cash_equivalents
            invested_capital_list.append((date, invested_capital))

            ebitda = income_statement_df.loc[date, 'ebitda']
            tax_rate = income_statement_df.loc[date, 'incomeBeforeTaxRatio']
            depreciation_and_amortization = income_statement_df.loc[date, 'depreciationAndAmortization']
            ebit = ebitda - depreciation_and_amortization
            nopat = ebit * (1 - tax_rate)

            roic = nopat / invested_capital * 100  # Convert ROIC to percentage
            roic_list.append((date, roic))

        roic_df = pd.DataFrame(roic_list, columns=['date', 'return on capital']).set_index('date')
        roic_df = roic_df.iloc[::-1]

        plt.figure(figsize=(10, 6))
        plt.bar(roic_df.index, roic_df['return on capital'], color='b', alpha=0.7)
        plt.title('Return on Invested Capital (ROIC) Over Time')
        plt.xlabel('Date')
        plt.ylabel('ROIC (%)')
        plt.grid(True)
        plt.xticks(rotation=90)
        
        # Customize y-axis ticks and labels to show percentage format
        plt.gca().set_yticklabels(['{:.0f}%'.format(x) for x in plt.gca().get_yticks()]) 
        
        plt.tight_layout()
        plt.show()
