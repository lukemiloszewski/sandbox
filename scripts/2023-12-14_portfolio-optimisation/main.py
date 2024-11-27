import pathlib

import pandas as pd

from pypfopt import EfficientFrontier, expected_returns, risk_models
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

root_path = pathlib.Path(__file__).parent.parent


def optimize_portfolio(stock_prices_df):
    """
    Find allocation with the maximum Sharpe ratio.
    """
    mean_historical_returns = expected_returns.mean_historical_return(stock_prices_df)
    sample_cov_matrix = risk_models.sample_cov(stock_prices_df)

    efficient_frontier = EfficientFrontier(mean_historical_returns, sample_cov_matrix)
    # max_sharpe_weights = efficient_frontier.max_sharpe()  # perform calculation on object
    cleaned_weights = efficient_frontier.clean_weights()

    return cleaned_weights, efficient_frontier


def allocate_portfolio(cleaned_weights, stock_prices_df, total_portfolio_value):
    """
    Allocate the total investment among the assets based on the optimized portfolio weights.
    """
    latest_prices = get_latest_prices(stock_prices_df)
    discrete_allocation = DiscreteAllocation(
        cleaned_weights, latest_prices, total_portfolio_value=total_portfolio_value
    )
    allocation, leftover = discrete_allocation.greedy_portfolio()

    return allocation, leftover


if __name__ == "__main__":
    stock_prices_file = str(root_path) + "/data/2023_12_14-stock_prices.csv"
    stock_prices_df = pd.read_csv(stock_prices_file, parse_dates=True, index_col="date")

    # Optimize portfolio
    optimized_weights, ef = optimize_portfolio(stock_prices_df)
    ef.save_weights_to_file(str(root_path) + "/data/2023_12_14-weights.csv")
    print("Optimized Portfolio Weights:", optimized_weights)
    ef.portfolio_performance(verbose=True)

    # Allocate portfolio
    total_investment = 10000
    allocation, funds_remaining = allocate_portfolio(
        optimized_weights, stock_prices_df, total_investment
    )
    print("Discrete allocation:", allocation)
    print(f"Funds remaining: ${funds_remaining:.2f}")
