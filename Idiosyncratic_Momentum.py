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
start_date = '2003-12-01'

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

# Download Fama French 5 factors model and Carhart momentum for factor spanning tests
five_factors = gff.famaFrench5Factor(frequency='m')
five_factors = five_factors.rename(columns={'date_ff_factors': 'date'})
five_factors['date'] = pd.to_datetime(five_factors['date']).dt.to_period('M').astype(str)
five_factors = five_factors.set_index('date')
five_factors = five_factors[start_date[:7]:]  # Slicing by 'YYYY-MM'

momentum = gff.momentumFactor(frequency='m')
momentum = momentum.rename(columns={'date_ff_factors': 'date'})
momentum['date'] = pd.to_datetime(momentum['date']).dt.to_period('M').astype(str)
momentum = momentum.set_index('date')
momentum = momentum[start_date[:7]:]  # Slicing by 'YYYY-MM'

# Download Fama French Factors with Monthly frequency from Kenneth French Website
factors = five_factors[['Mkt-RF', 'SMB', 'HML', 'RF']]

# Align the indices of stock_returns and factors
common_dates = stock_returns.index.intersection(factors.index)
stock_returns = stock_returns.loc[common_dates]
factors = factors.loc[common_dates]
momentum = momentum.loc[common_dates]

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

# Drop rows (months) with all NaN values in momentum_scores
momentum_scores = momentum_scores.dropna(how='all')
# Initialize DataFrames to store decile portfolio returns and WML returns
decile_returns = pd.DataFrame(index=momentum_scores.index, columns=range(1, 11))
wml_returns = pd.DataFrame(index=momentum_scores.index, columns=["WML"])

# Loop over each month in momentum_scores.index to calculate decile portfolio returns
for i in momentum_scores.index:
    # Get the iMOM rankings for the current month
    current_month = i
    rankings = momentum_scores.loc[current_month].dropna().rank()  # Drop NaN values for individual stocks

    # Divide rankings into 10 deciles
    deciles = pd.qcut(rankings, 10, labels=False) + 1  # Deciles from 1 (lowest) to 10 (highest)

    # Calculate returns for each decile
    for decile in range(1, 11):
        decile_stocks = rankings.index[deciles == decile]
        decile_stocks = decile_stocks[decile_stocks.isin(stock_returns.columns)]  # Ensure alignment with stock returns

        # Calculate mean return for the decile in the current month
        decile_return = stock_returns.loc[current_month, decile_stocks].mean()
        decile_returns.loc[current_month, decile] = decile_return

# Calculate the WML (long top decile, short bottom decile) outside the loop
wml_returns["WML"] = decile_returns[10] - decile_returns[1]

# Performances of decile portfolios
decile_portfolios = pd.DataFrame(index=decile_returns.columns)
decile_portfolios['Mean'] = decile_returns.mean(axis=0) * 12
decile_portfolios['Std Dev'] = decile_returns.std(axis=0) * np.sqrt(12)
rf_annualized = factors['RF'].mean() * 12  # Annualize the risk-free rate needs adjustment
decile_portfolios['Sharpe Ratio'] = (decile_portfolios['Mean'] - rf_annualized) / decile_portfolios['Std Dev']

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
    'MOM': momentum['MOM'],
    'RF': factors['RF']
})
summary_stats = pd.DataFrame()
summary_stats['Mean'] = combined_data[['WML', 'Mkt-RF', 'SMB', 'HML', 'MOM']].mean() * 12
summary_stats['Std Dev'] = combined_data[['WML', 'Mkt-RF', 'SMB', 'HML', 'MOM']].std() * np.sqrt(12)
rf_annualized = combined_data['RF'].mean() * 12  # Annualize the risk-free rate
summary_stats['Sharpe Ratio'] = (summary_stats['Mean'] - rf_annualized) / summary_stats['Std Dev']

factors_aug = factors.merge(momentum, left_index=True, right_index=True)
factors_aug = factors_aug.merge(wml_returns, left_index=True, right_index=True)
factors_aug['WML'] = pd.to_numeric(factors_aug['WML'], errors='coerce')
factors_aug.corr()

# Calculate cumulative returns for WML, Mkt-RF, SMB, HML and MOM
wml_cum_returns = (1 + wml_returns).cumprod() - 1
mkt_rf_cum_returns = (1 + factors['Mkt-RF']).cumprod() - 1
smb_cum_returns = (1 + factors['SMB']).cumprod() - 1
hml_cum_returns = (1 + factors['HML']).cumprod() - 1
mom_cum_returns = (1 + momentum).cumprod() - 1

# Step 2: Plot idiosyncratic and total return momentum
plt.figure(figsize=(10, 6))
plt.plot(wml_cum_returns.index, wml_cum_returns.values, label='WML (iMOM)', color='blue', linewidth=2)
plt.plot(mom_cum_returns.index, mom_cum_returns.values, label='MOM', color='orange', linewidth=2)
plt.title('Cumulative Returns: WML (iMOM) vs Total Return Momentum')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.legend()
# Show plot
plt.show()

# Step 3: Plot WML and Fama-French 3 factors on the same graph
plt.figure(figsize=(10, 6))
plt.plot(wml_cum_returns.index, wml_cum_returns.values, label='WML (iMOM)', color='blue', linewidth=2)
plt.plot(mkt_rf_cum_returns.index, mkt_rf_cum_returns.values,
         label='Mkt-RF', color='red', linestyle='--', linewidth=1.5)
plt.plot(smb_cum_returns.index, smb_cum_returns.values, label='SMB', color='green', linestyle='--', linewidth=1.5)
plt.plot(hml_cum_returns.index, hml_cum_returns.values, label='HML', color='orange', linestyle='--', linewidth=1.5)

# Add title, labels and legend
plt.title('Cumulative Returns: WML (iMOM) vs Fama-French 3 Factors')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.legend()

# Show plot
plt.show()
