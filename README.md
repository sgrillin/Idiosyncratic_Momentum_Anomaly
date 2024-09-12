# Idiosyncratic Momentum Anomaly

This repository contains Python code that replicates the idiosyncratic momentum factor by Blitz et al. (2020), *"The Idiosyncratic Momentum Anomaly."* The paper explores the idiosyncratic momentum factor and its impact on stock performance, building on existing research on momentum strategies.

## Overview

The **Idiosyncratic Momentum Anomaly** is a unique factor that captures momentum in the idiosyncratic component of stock returns. The paper demonstrates how idiosyncratic momentum, when isolated from systematic factors, exhibits strong predictive power for future stock returns.

This project replicates the following aspects from the paper:

- Downloading stock price data for the S&P 500 stocks.
- Calculating **idiosyncratic returns** by running rolling regressions on the Fama-French 3 factors.
- Creating a **momentum score** for each stock based on idiosyncratic returns.
- Constructing a **WML (Winner Minus Loser)** factor by going long on the top decile of stocks and short on the bottom decile.
- Comparing the performance of the WML factor with the **Fama-French 3 factors** (Mkt-RF, SMB, HML).

## Key Features

- **Data Download**: Uses Yahoo Finance to download historical stock price data for the S&P 500.
- **Rolling Regressions**: Performs rolling regressions over a 36-month window to calculate idiosyncratic returns.
- **Momentum Score**: Calculates the momentum score for each stock based on the past 12 months' idiosyncratic returns.
- **Performance Comparison**: Compares the cumulative returns of the WML factor with the Fama-French factors (Mkt-RF, SMB, HML).
- **Plotting**: Visualizes the cumulative returns for the WML factor and the Fama-French factors.

## Setup

### Prerequisites

To run the code, ensure you have the following Python libraries installed:

- `pandas`
- `numpy`
- `yfinance`
- `statsmodels`
- `matplotlib`
- `joblib` (optional for parallel processing)
- `getFamaFrenchFactors` (for downloading Fama-French factors)

You can install the necessary libraries using:

```bash
pip install pandas numpy yfinance statsmodels matplotlib joblib getFamaFrenchFactors
```
## Running the Code
Clone this repository:
```bash
git clone https://github.com/sgrillin/Idiosyncratic_Momentum_Anomaly.git
```

Open the project folder and run the main Python script to replicate the results from the paper:
```bash
python idiosyncratic_momentum.py
```

The script will:
- Download historical stock prices from Yahoo Finance for the S&P 500.
- Compute the idiosyncratic returns based on the Fama-French 3 factors.
- Create the momentum score and build the WML factor.
- Plot the cumulative returns of the WML factor and compare them with the Fama-French factors.

## Results
The results include:

- Cumulative Returns Plot: A visualization of the cumulative returns for the WML factor versus the Fama-French 3 factors.
- Sharpe Ratio and Summary Statistics: A table displaying the mean, standard deviation, and Sharpe ratio for the WML factor and the Fama-French factors.

## References
Blitz, David, Matthias X. Hanauer, and Milan Vidojevic. "The idiosyncratic momentum anomaly." International Review of Economics & Finance 69 (2020): 932-957.

https://www.sciencedirect.com/science/article/abs/pii/S1059056020300927

## Contributions
Feel free to submit a pull request if you'd like to contribute to improving the code or adding new features.
