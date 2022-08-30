# Python-Stock-Assess
`finance.py` is a program which is built to assess publicly traded stock to assist one's investing habit. Note: this project was done primarily out of an interest for Python, and is not intended to greatly influence anyone's investing decisions, especially as it has been created by an amatuer. The project is incomplete but at a functional stage.

# Required Packages
- `yfinance`
- `pandas`
- `csv`
- `warnings`
- `time`
- `os`
- `tkinter` 
- `threading` 
- `requests`
- `PIL` 
- `mplfinance` 
- `tempfile` 
- `shutil`
- `sec_api` 
- `fredapi`

# Usage
Upon execution, a GUI should appear. At the bottom right a list should appear with the options `Stocks` or `Check Symbols`. Initially the user should select `Stocks` and the program will begin assessing publicly listed stocks. `Check Stocks` will reassess the existing list of stocks which the program has identified as desireable. When a stock is determined to be desireable it will appear in the list box to the right. Selecting the ticker symbol will provide a graph of the stock's performance over the past two years. Note: while the program is running, it is pulling SEC filings from the EDGAR database and writing them to CSV files; this feature is for future functionality.

# Other Requirement
The program does use an API which requires a subscription, `sec-api`. An account and subscription can be located [here](https://sec-api.io/register). Users will recieve an API key which can be entered in lines 413 and 428 of the program: `qapi = sapi.QueryApi(api_key='api_key_goes_here')` and `xapi = sapi.XbrlApi(api_key='api_key_goes_here')` respectively.
