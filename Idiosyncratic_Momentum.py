import backtrader as bt
import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
import datetime
import getFamaFrenchFactors as gff
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Download SPX stocks from Yahoo Finance and calculate monthly returns
sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
sp500_list = np.array(sp500[0]['Symbol'])
start_date = '2013-12-01'

df = pd.DataFrame(columns=sp500_list)
for i in df.columns:
    try:
        df[i] = yf.download(
            i,
            start=start_date,
            end=pd.Timestamp(datetime.date.today())
        )['Adj Close']
        print(f'{i} is successfully extracted')
    except Exception as e:
        print(f'Error downloading {i}: {e}')

# We remove stocks that we could not extract from yfinance
nan_stocks_list = [col for col in df if df[col].isna().sum() > 0]
stock_prices = df.drop(nan_stocks_list, axis=1)

# Resample to monthly frequency using the last business day of each month
monthly_df = stock_prices.resample('M').last()

# Convert the index to 'YYYY-MM' format
monthly_df.index = monthly_df.index.to_period('M').strftime('%Y-%m')

# Calculate monthly returns as the log difference
stock_returns = np.log(monthly_df / monthly_df.shift(1)).dropna()

# Download Fama and French Factors with Monthly frequency from Kenneth French Website
factors = gff.famaFrench3Factor(frequency='m')
factors = factors.rename(columns={'date_ff_factors': 'date'})
factors['date'] = pd.to_datetime(factors['date']).dt.to_period('M').astype(str)
factors = factors.set_index('date')
factors = factors[start_date[:7]:]  # Slicing by 'YYYY-MM'

# Align the indices of stock_returns and factors
common_dates = stock_returns.index.intersection(factors.index)
stock_returns = stock_returns.loc[common_dates]
factors = factors.loc[common_dates]

# Calculate idiosyncratic returns
# Initialize DataFrame to store residuals (idiosyncratic returns)
idio_returns = pd.DataFrame(index=stock_returns.index, columns=stock_returns.columns)

# Rolling regression with a 36-month window to extract residuals (idiosyncratic returns)
for stock, returns_series in stock_returns.items():
    # Loop over time windows (36-month rolling window)
    for i in range(36, len(returns_series)):
        # Get the excess returns (subtracting risk-free rate)
        excess_returns = returns_series.iloc[i-36:i] - factors['RF'].iloc[i-36:i]  # Last 36 months

        # Get the corresponding factors (Mkt-RF, SMB, HML)
        X = factors[['Mkt-RF', 'SMB', 'HML']].iloc[i-36:i]
        X = sm.add_constant(X)  # Add constant for the regression

        # Run the regression
        model = sm.OLS(excess_returns, X).fit()

        # Store the residual (idiosyncratic return) for the last month in the window
        current_month = stock_returns.index[i]
        idio_returns.loc[current_month, stock] = model.resid[-1]  # Residual for the last month of the window

# Step 2: Calculate momentum scores (average of residuals from t-12 to t-2)
momentum_scores = pd.DataFrame(index=stock_returns.index, columns=stock_returns.columns)

for stock, residuals_series in idio_returns.items():
    for i in range(12, len(residuals_series)):
        # Get the residuals from t-12 to t-2 (ignoring t-1)
        residuals = residuals_series.iloc[i-12:i-1]  # Last 11 months of residuals

        if len(residuals) == 11:  # Ensure we have enough data
            # Calculate the mean of the residuals
            residual_mean = residuals.mean()

            # Numerator: Sum of residuals from t-12 to t-2
            numerator = residuals.sum()

            # Denominator: Square root of the sum of squared deviations from the mean
            denominator = np.sqrt(((residuals - residual_mean) ** 2).sum())

            # Calculate momentum score
            if denominator != 0:  # Avoid division by zero
                momentum_scores.iloc[i, momentum_scores.columns.get_loc(stock)] = numerator / denominator
            else:
                momentum_scores.iloc[i, momentum_scores.columns.get_loc(stock)] = np.nan

# Initialize DataFrame to store WML factor returns
wml_returns = pd.DataFrame(index=stock_returns.index, columns=["WML"])

# Loop over each month in momentum_scores.index to calculate the WML factor
for i in momentum_scores.index:
    # Get the iMOM rankings for the current month
    current_month = i
    rankings = momentum_scores.loc[current_month].rank()

    # Top decile (Winners): Stocks with the highest momentum scores (top 10%)
    top_decile = rankings[rankings > rankings.quantile(0.9)]

    # Bottom decile (Losers): Stocks with the lowest momentum scores (bottom 10%)
    bottom_decile = rankings[rankings < rankings.quantile(0.1)]

    # Ensure top_decile and bottom_decile are aligned with stock_returns columns
    top_decile = top_decile[top_decile.index.isin(stock_returns.columns)]
    bottom_decile = bottom_decile[bottom_decile.index.isin(stock_returns.columns)]

    # Calculate returns for the current month
    long_returns = stock_returns.loc[current_month, top_decile.index].mean()
    short_returns = stock_returns.loc[current_month, bottom_decile.index].mean()

    # Calculate WML (long top decile, short bottom decile)
    wml_returns.loc[current_month, "WML"] = long_returns - short_returns


# Summary statistics and graph the performances of the WML and other factors
# Step 1: Align the dates for both WML and Fama-French factors
wml_returns = wml_returns.dropna(axis=0)
common_dates = wml_returns.index.intersection(factors.index)
wml_returns = wml_returns.loc[common_dates]
factors = factors.loc[common_dates]

# Summary stats
combined_data = pd.DataFrame({
    'WML': wml_returns['WML'],
    'Mkt-RF': factors['Mkt-RF'],
    'SMB': factors['SMB'],
    'HML': factors['HML'],
    'RF': factors['RF']
})
summary_stats = pd.DataFrame()
summary_stats['Mean'] = combined_data[['WML', 'Mkt-RF', 'SMB', 'HML']].mean() * 12  # Multiply by 12 to annualize
summary_stats['Std Dev'] = combined_data[['WML', 'Mkt-RF', 'SMB', 'HML']].std() * np.sqrt(12)  # Multiply by sqrt(12) to annualize
rf_annualized = combined_data['RF'].mean() * 12  # Annualize the risk-free rate
summary_stats['Sharpe Ratio'] = (summary_stats['Mean'] - rf_annualized) / summary_stats['Std Dev']
summary_stats

# Calculate cumulative returns for WML, Mkt-RF, SMB, and HML
wml_cum_returns = (1 + wml_returns).cumprod() - 1
mkt_rf_cum_returns = (1 + factors['Mkt-RF']).cumprod() - 1
smb_cum_returns = (1 + factors['SMB']).cumprod() - 1
hml_cum_returns = (1 + factors['HML']).cumprod() - 1

# Step 3: Plot WML and Fama-French 3 factors on the same graph
plt.figure(figsize=(10, 6))
plt.plot(wml_cum_returns.index, wml_cum_returns.values, label='WML (iMOM)', color='blue', linewidth=2)
plt.plot(mkt_rf_cum_returns.index, mkt_rf_cum_returns.values, label='Mkt-RF', color='red', linestyle='--', linewidth=1.5)
plt.plot(smb_cum_returns.index, smb_cum_returns.values, label='SMB', color='green', linestyle='--', linewidth=1.5)
plt.plot(hml_cum_returns.index, hml_cum_returns.values, label='HML', color='orange', linestyle='--', linewidth=1.5)

# Add title, labels and legend
plt.title('Cumulative Returns: WML (iMOM) vs Fama-French 3 Factors')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.legend()

# Show plot
plt.show()

# Convert the index of wml_returns to DatetimeIndex
wml_returns.index = pd.to_datetime(wml_returns.index, format='%Y-%m')

# Backtrader Strategy
class WMLStrategy(bt.Strategy):
    params = dict(
        lookback=1,  # Lookback period for the strategy (1 month)
        printlog=False  # Whether to print log information
    )

    def __init__(self):
        # Keep track of WML factor in the strategy
        self.wml = self.datas[0].close

    def next(self):
        # Simple long-short strategy based on WML factor
        if self.wml[0] > 0:  # If WML is positive, go long
            self.order_target_percent(target=1.0)  # Allocate 100% of portfolio to this
        elif self.wml[0] < 0:  # If WML is negative, go short
            self.order_target_percent(target=-1.0)  # Allocate 100% of portfolio to short
        else:
            self.order_target_percent(target=0)  # Exit all positions if WML is zero

    def log(self, txt, dt=None):
        ''' Logging function for this strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} {txt}')

    def stop(self):
        ''' Called at the end of the backtest '''
        if self.params.printlog:
            print(f'Ending Value: {self.broker.getvalue():.2f}')

# Step 1: Prepare WML data for Backtrader
# Ensure WML data is in the correct format for Backtrader
wml_bt_data = bt.feeds.PandasData(dataname=wml_returns)

# Step 2: Create a Cerebro engine
cerebro = bt.Cerebro()

# Add the WML data feed
cerebro.adddata(wml_bt_data)

# Add the WMLStrategy to the engine
cerebro.addstrategy(WMLStrategy)

# Set the starting cash for the portfolio
cerebro.broker.set_cash(1000000)  # Starting with $1 million

# Set broker commission (optional, but realistic)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission per trade

# Step 3: Run the backtest
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Step 4: Plot the result
cerebro.plot()

# Ensure WML data is in the correct format for Backtrader
wml_bt_data = bt.feeds.PandasData(dataname=wml_returns)

# Step 2: Create a Cerebro engine
cerebro = bt.Cerebro()

# Add the WML data feed
cerebro.adddata(wml_bt_data)

# Add the WMLStrategy to the engine
cerebro.addstrategy(WMLStrategy)

# Set the starting cash for the portfolio
cerebro.broker.set_cash(1000000)  # Starting with $1 million

# Set broker commission (optional, but realistic)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission per trade

# Step 3: Run the backtest
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Step 4: Plot the result
cerebro.plot()