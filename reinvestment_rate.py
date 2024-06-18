import requests
from dotenv import load_dotenv
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

            period_str = f'period={period}&' if period and (period == 'quarterly' or period == 'annual') else ''

            url = f"https://financialmodelingprep.com/api/{version}/{endpoint}/{ticker_symbol}?{period_str}apikey={api_key}"
            print(f"Request URL: {url}") 
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Failed to fetch data: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

if __name__ == "__main__":
    ticker = "AAPL"
    graph = Graphing(ticker)
    balance_sheet = graph.request_fmp_api('v3', 'balance-sheet-statement', ticker, 'quarterly')
    income_statement = graph.request_fmp_api('v3', 'income-statement', ticker, 'quarterly')
    cash_flow_statement = graph.request_fmp_api('v3', 'cash-flow-statement', ticker, 'quarterly')

    if balance_sheet and income_statement and cash_flow_statement:
        balance_sheet_df = pd.DataFrame(balance_sheet).set_index('date')
        income_statement_df = pd.DataFrame(income_statement).set_index('date')
        cash_flow_statement_df = pd.DataFrame(cash_flow_statement).set_index('date')
    else:
        print("ERROR WITH DATAFRAMES")
        exit(1)

    reinvestment_rate_list = []
    for date in cash_flow_statement_df.index[:20]:
        depreciation_and_amortization = cash_flow_statement_df.loc[date, 'depreciationAndAmortization']
        capex = cash_flow_statement_df.loc[date, 'capitalExpenditure']
        net_capex = capex - depreciation_and_amortization 

        change_in_working_capital = cash_flow_statement_df.loc[date, 'changeInWorkingCapital']

        ebitda = income_statement_df.loc[date, 'ebitda']
        tax_rate = income_statement_df.loc[date, 'incomeTaxExpense'] / income_statement_df.loc[date, 'incomeBeforeTax']
        depreciation_and_amortization = income_statement_df.loc[date, 'depreciationAndAmortization']
        ebit = ebitda - depreciation_and_amortization
        nopat = ebit * (1 - tax_rate)

        reinvestment_rate = (net_capex + change_in_working_capital) / nopat
        reinvestment_rate_list.append((date, reinvestment_rate))

    if not reinvestment_rate_list:
        print("No data to plot")
        exit(1)

    reinvestment_df = pd.DataFrame(reinvestment_rate_list, columns=['date', 'reinvestment rate']).set_index('date')

    plt.figure(figsize=(10, 6))
    plt.bar(reinvestment_df.index, reinvestment_df['reinvestment rate'], color='b', alpha=0.7)
    plt.title('Reinvestment rate Over Time')
    plt.xlabel('Date')
    plt.ylabel('Reinvestment (%)')
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.gca().set_yticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_yticks()])
    plt.tight_layout()
    plt.show()
