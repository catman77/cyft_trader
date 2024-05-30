# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)
# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib
from functools import reduce
from freqtrade.strategy import IStrategy
from freqtrade.strategy.interface import IStrategy


class MeanReversionStrategy(IStrategy):

    @property
    def plot_config(self):
        return {
            'main_plot': {
            },
            'subplots': {
                'Return': {
                    'return': {'color': 'yellow'},
                    f'wbb_upperband_{self.wbb_window.value}_{self.wbb_stds.value}': {'color': 'green'},
                    f'wbb_lowerband_{self.wbb_window.value}_{self.wbb_stds.value}': {'color': 'green'},
                    f'wbb_middleband_{self.wbb_window.value}_{self.wbb_stds.value}': {'color': 'green'}
                },
            },
        }

    # Config
    INTERFACE_VERSION: int = 3
    startup_candle_count: int = 60
    process_only_new_candles = True
    can_short: bool = True
    timeframe = "15m"

    # Position config
    position_adjustment_enabled = True
    max_entry_position_adjustment = 3
    max_dca_multiplier = 5.5    

    # These values can be overridden in the config.
    use_exit_signal = False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # ROI table:
    minimal_roi = {
        "0":  0.288,
        "41": 0.131,
        "120": 0.032,
        "429": 0
    }

    # Stoploss:
    stoploss = -0.16

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.175
    trailing_stop_positive_offset = 0.194
    trailing_only_offset_is_reached = True

    # hyperspace params:
    volume_mean_window = IntParameter(5, 50, default=16, space='buy')
    volume_stds_window = IntParameter(5, 50, default=49, space='buy')
    wbb_window = IntParameter(5, 60, default=36, space='buy')
    wbb_stds = IntParameter(1, 3, default=2, space='buy')

    # def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
    #                         proposed_stake: float, min_stake: Optional[float], max_stake: float,
    #                         leverage: float, entry_tag: Optional[str], side: str,
    #                         **kwargs) -> float:
    #     return 0.5
    
    # def adjust_trade_position(self, trade: Trade, current_time: datetime,
    #                           current_rate: float, current_profit: float,
    #                           min_stake: Optional[float], max_stake: float,
    #                           current_entry_rate: float, current_exit_rate: float,
    #                           current_entry_profit: float, current_exit_profit: float,
    #                           **kwargs
    #                           ) -> Union[Optional[float], Tuple[Optional[float], Optional[str]]]:
    #     """
    #     Custom trade adjustment logic, returning the stake amount that a trade should be
    #     increased or decreased.
    #     This means extra entry or exit orders with additional fees.
    #     Only called when `position_adjustment_enable` is set to True.

    #     For full documentation please go to https://www.freqtrade.io/en/latest/strategy-advanced/

    #     When not implemented by a strategy, returns None

    #     :param trade: trade object.
    #     :param current_time: datetime object, containing the current datetime
    #     :param current_rate: Current entry rate (same as current_entry_profit)
    #     :param current_profit: Current profit (as ratio), calculated based on current_rate 
    #                            (same as current_entry_profit).
    #     :param min_stake: Minimal stake size allowed by exchange (for both entries and exits)
    #     :param max_stake: Maximum stake allowed (either through balance, or by exchange limits).
    #     :param current_entry_rate: Current rate using entry pricing.
    #     :param current_exit_rate: Current rate using exit pricing.
    #     :param current_entry_profit: Current profit using entry pricing.
    #     :param current_exit_profit: Current profit using exit pricing.
    #     :param **kwargs: Ensure to keep this here so updates to this won't break your strategy.
    #     :return float: Stake amount to adjust your trade,
    #                    Positive values to increase position, Negative values to decrease position.
    #                    Return None for no action.
    #                    Optionally, return a tuple with a 2nd element with an order reason
    #     """

    #     if current_profit > 0.05 and trade.nr_of_successful_exits == 0:
    #         # Take half of the profit at +5%
    #         return -(trade.stake_amount / 2), 'half_profit_5%'

    #     if current_profit > -0.05:
    #         return None

    #     # Obtain pair dataframe (just to show how to access it)
    #     dataframe, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
    #     # Only buy when not actively falling price.
    #     last_candle = dataframe.iloc[-1].squeeze()
    #     previous_candle = dataframe.iloc[-2].squeeze()
    #     if last_candle['close'] < previous_candle['close']:
    #         return None

    #     filled_entries = trade.select_filled_orders(trade.entry_side)
    #     count_of_entries = trade.nr_of_successful_entries
    #     # Allow up to 3 additional increasingly larger buys (4 in total)
    #     # Initial buy is 1x
    #     # If that falls to -5% profit, we buy 1.25x more, average profit should increase to roughly -2.2%
    #     # If that falls down to -5% again, we buy 1.5x more
    #     # If that falls once again down to -5%, we buy 1.75x more
    #     # Total stake for this trade would be 1 + 1.25 + 1.5 + 1.75 = 5.5x of the initial allowed stake.
    #     # That is why max_dca_multiplier is 5.5
    #     # Hope you have a deep wallet!
    #     try:
    #         # This returns first order stake size
    #         stake_amount = filled_entries[0].stake_amount
    #         # This then calculates current safety order size
    #         stake_amount = stake_amount * (1 + (count_of_entries * 0.25))
    #         return stake_amount, '1/3rd_increase'
    #     except Exception as exception:
    #         return None

    #     return None

    # Indicators generating function
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # return dataframe
        dataframe['return'] = dataframe['close'].pct_change()

        volume_frames = [dataframe]
        for mean in self.volume_mean_window.range:
            for stds in self.volume_stds_window.range:
                rolling_mean = dataframe['volume'].rolling(mean).mean()
                rolling_std = dataframe['volume'].rolling(stds).std()
                volume_frames.append(DataFrame({
                    f'volume_threshold_{mean}_{stds}': rolling_mean + (2.5 * rolling_std)
                }))
        dataframe = pd.concat(volume_frames, axis=1)

        wbb_frames = [dataframe]
        for window in self.wbb_window.range:
            for stds in self.wbb_stds.range:
                weighted_bollinger = qtpylib.weighted_bollinger_bands(
                    dataframe['return'], window=window, stds=stds)
                wbb_frames.append(DataFrame({
                    f"wbb_upperband_{window}_{stds}": weighted_bollinger["upper"],
                    f"wbb_lowerband_{window}_{stds}": weighted_bollinger["lower"],
                    f"wbb_middleband_{window}_{stds}": weighted_bollinger["mid"]
                }))
        dataframe = pd.concat(wbb_frames, axis=1)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Long (Buy) signal conditions
        long_conditions = []
        long_conditions.append(qtpylib.crossed_above(
            dataframe[f"wbb_lowerband_{self.wbb_window.value}_{self.wbb_stds.value}"], dataframe['return']
        ))
        long_conditions.append(
            dataframe['volume'] > 0.9 * dataframe[f"volume_threshold_{self.volume_mean_window.value}_{self.volume_stds_window.value}"])
        long_conditions.append(
            dataframe['return'] < 4.5 * dataframe[f"volume_threshold_{self.volume_mean_window.value}_{self.volume_stds_window.value}"])

        dataframe.loc[reduce(lambda x, y: x & y,
                             long_conditions), 'enter_long'] = 1

        short_conditions = []
        short_conditions.append(qtpylib.crossed_above(
            dataframe['return'], dataframe[f"wbb_upperband_{self.wbb_window.value}_{self.wbb_stds.value}"]
        ))
        short_conditions.append(
            dataframe['volume'] > 0.9 * dataframe[f"volume_threshold_{self.volume_mean_window.value}_{self.volume_stds_window.value}"])
        short_conditions.append(
            dataframe['volume'] < 4.5 * dataframe[f"volume_threshold_{self.volume_mean_window.value}_{self.volume_stds_window.value}"])

        dataframe.loc[reduce(lambda x, y: x & y,
                             short_conditions), 'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str,
                 **kwargs) -> float:
        return 2.3

# # Buy hyperspace params:
#     buy_params = {
#         "volume_mean_window": 16,
#         "volume_stds_window": 49,
#         "wbb_stds": 2,
#         "wbb_window": 36,
#     }

#     # ROI table:
#     minimal_roi = {
#         "0": 0.288,
#         "41": 0.131,
#         "120": 0.032,
#         "429": 0
#     }

#     # Stoploss:
#     stoploss = -0.16

#     # Trailing stop:
#     trailing_stop = True
#     trailing_stop_positive = 0.175
#     trailing_stop_positive_offset = 0.194
#     trailing_only_offset_is_reached = True
    

#     # Max Open Trades:
#     max_open_trades = 5  # value loaded from strategy