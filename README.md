# Idiosyncratic Momentum Anomaly

This repository contains Python code that replicates the paper by Blitz et al. (2011), *"The Idiosyncratic Momentum Anomaly."* The paper explores the idiosyncratic momentum factor and its impact on stock performance, building on existing research on momentum strategies.

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
