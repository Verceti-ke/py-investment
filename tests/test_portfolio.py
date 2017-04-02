import pytest

import pytech.data.handler
from pytech.fin.portfolio import Portfolio, BasicPortfolio
from pytech.backtest.event import MarketEvent


class TestPortfolio(object):

    def test_check_liquidity(self):

        test_portfolio = Portfolio(starting_cash=100)

        liquid = test_portfolio.check_liquidity(100.0, 2)
        assert liquid is False

        liquid = test_portfolio.check_liquidity(100.0, -2)
        assert liquid is True

        liquid = test_portfolio.check_liquidity(1.0, 2)
        assert liquid is True


class TestBasicPortfolio(object):

    def test_constructor(self, yahoo_data_handler, events, blotter, start_date):
        test_portfolio = BasicPortfolio(yahoo_data_handler, events,
                                        start_date, blotter)
        assert test_portfolio is not None

    def test_update_timeindex(self, basic_portfolio):
        """
        Test updating the time index.
        
        :param BasicPortfolio basic_portfolio: 
        """
        basic_portfolio.update_timeindex(MarketEvent())
        print(basic_portfolio.current_positions)
        print(basic_portfolio.current_holdings)
        print(basic_portfolio.all_holdings)
        print(basic_portfolio.all_positions)

