import datetime as dt
import logging
import queue

import pytech.utils as utils
from pytech.data.handler import Bars
from pytech.fin.portfolio import BasicPortfolio
from pytech.trading.blotter import Blotter
from pytech.trading.execution import SimpleExecutionHandler
from pytech.utils.enums import EventType
from pytech.utils import DateRange


class Backtest(object):
    """
    Does backtest stuff...

    update me. plz upd8 me.
    """

    def __init__(
        self,
        ticker_list,
        initial_capital,
        date_range: DateRange,
        strategy,
        data_handler=None,
        execution_handler=None,
        portfolio=None,
        balancer=None,
    ):
        """
        Initialize the backtest.

        :param iterable ticker_list: A list of tickers.
        :param initial_capital: Amount of starting capital.
        :param start_date: The date to start the backtest as of.
        :param strategy: The strategy to backtest.
        :param data_handler:
        :param execution_handler:
        :param portfolio:
        """
        self.logger = logging.getLogger(__name__)
        self.ticker_list = utils.iterable_to_set(ticker_list)
        self.initial_capital = initial_capital
        self.date_range = date_range or DateRange()

        self.strategy_cls = strategy

        if data_handler is None:
            self.data_handler_cls = Bars
        else:
            self.data_handler_cls = data_handler

        if execution_handler is None:
            self.execution_handler_cls = SimpleExecutionHandler
        else:
            self.execution_handler_cls = execution_handler

        if portfolio is None:
            self.portfolio_cls = BasicPortfolio
        else:
            self.portfolio_cls = portfolio

        self.events = queue.Queue()

        self.blotter = Blotter(self.events)

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self._init_trading_instances()

    def _init_trading_instances(self):
        self.data_handler = self.data_handler_cls(
            self.events, self.ticker_list, self.date_range
        )
        self.blotter.bars = self.data_handler
        self.strategy = self.strategy_cls(self.data_handler, self.events)
        self.portfolio = self.portfolio_cls(
            self.data_handler,
            self.events,
            self.date_range,
            self.blotter,
            self.initial_capital,
        )
        self.execution_handler = self.execution_handler_cls(self.events)

    def pre_run_hook(self):
        """
        Override this function if you wish you change the configuration
        of the backtest before running.

        This method gets called in ``run``.
        """

    def run(self):
        self.pre_run_hook()
        iterations = 0

        while True:
            iterations += 1
            self.logger.info(f"Iteration #{iterations}")

            try:
                self.data_handler.update_bars()
            except StopIteration:
                break

            # handle events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    self.logger.info("Continuing to next day.")
                    break

                if event is not None:
                    self._process_event(event)

    def _process_event(self, event) -> None:
        self.logger.debug(f"Processing {event.event_type}")

        if event.event_type is EventType.MARKET:
            self.strategy.generate_signals(event)
            self.portfolio.update_timeindex(event)
        elif event.event_type is EventType.SIGNAL:
            self.signals += 1
            self.portfolio.update_signal(event)
        elif event.event_type is EventType.TRADE:
            self.orders += 1
            self.execution_handler.execute_order(event)
        elif event.event_type is EventType.FILL:
            self.fills += 1
            self.portfolio.update_fill(event)
