"""
engine.py: The Core Footprint Processing Engine

This module contains the main FootprintEngine class, which is responsible
for processing raw tick data into structured FootprintBar objects according
to the specified configuration.
"""

import pandas as pd
import numpy as np
import time
import logging
import pickle
from datetime import datetime, timedelta
from typing import Optional, List, Any

# Import from our new local modules
from .config import FootprintEngineConfig
from .domain import FootprintBar, PriceLevelData, AggregationType

# Setup logging for the engine
logger = logging.getLogger(__name__)

class FootprintEngine:
    """Processes tick data to construct and manage footprint bars."""

    def __init__(self, config: FootprintEngineConfig):
        """Initializes the engine with a given configuration."""
        self.config = config
        self.bars: List[FootprintBar] = []
        self.current_bar: Optional[FootprintBar] = None
        self._total_ticks_processed = 0
        logger.info(
            f"FootprintEngine initialized. Aggregation: {config.aggregation_type.value} "
            f"({config.aggregation_value}), Tick Size: {config.tick_size}"
        )

    def process_tick(self, timestamp: datetime, price: float, volume: int, is_bid_trade: bool) -> None:
        """Processes a single market tick and updates the current bar."""
        self._total_ticks_processed += 1

        if self.current_bar is None or self._should_create_new_bar(timestamp, price):
            if self.current_bar is not None:
                self._finalize_current_bar()
            self._create_new_bar(timestamp, price)

        # This should never happen, but as a safeguard:
        if self.current_bar is None:
            logger.error("Critical error: current_bar is None after creation attempt.")
            return

        # Aggregate tick data into the correct price level
        rounded_price = round(price / self.config.tick_size) * self.config.tick_size
        if rounded_price not in self.current_bar.price_levels:
            self.current_bar.price_levels[rounded_price] = PriceLevelData(price=rounded_price)

        level_data = self.current_bar.price_levels[rounded_price]
        if is_bid_trade:  # Seller was aggressive
            level_data.bid_volume += volume
            level_data.bid_trades += 1
        else:  # Buyer was aggressive
            level_data.ask_volume += volume
            level_data.ask_trades += 1
        
        level_data.update_derived_metrics(self.config.get_zero_handling_for_ratios())

        # Update bar's OHLC, time, and aggregation counters
        self.current_bar.high_price = max(self.current_bar.high_price, rounded_price)
        self.current_bar.low_price = min(self.current_bar.low_price, rounded_price)
        self.current_bar.close_price = rounded_price
        self.current_bar.end_time = timestamp
        self.current_bar.tick_count += 1
        self.current_bar.current_aggregated_volume += volume

    def process_tick_batch(self, ticks_df: pd.DataFrame) -> None:
        """Processes a batch of ticks from a pandas DataFrame for high-performance backtesting."""
        logger.info(f"Processing batch of {len(ticks_df)} ticks...")
        # Use itertuples for a significant performance boost over iterrows
        for tick in ticks_df.itertuples(index=False):
            self.process_tick(
                timestamp=tick.datetime,
                price=tick.price,
                volume=tick.volume,
                is_bid_trade=tick.is_bid_trade,
            )
        
        # After a batch, the last bar is still 'current'. We can update its stats
        # to reflect the latest state, but it's only finalized when a *new* bar starts.
        if self.current_bar:
            self.current_bar.update_bar_statistics(self.config.value_area_percentage)
        logger.info("Batch processing complete.")

    def _should_create_new_bar(self, timestamp: datetime, price: float) -> bool:
        """Determines if the current tick should trigger the creation of a new bar."""
        agg_type = self.config.aggregation_type
        agg_val = self.config.aggregation_value

        if agg_type == AggregationType.TIME:
            interval_end = pd.Timestamp(self.current_bar.start_time) + pd.Timedelta(str(agg_val))
            return timestamp >= interval_end
        elif agg_type == AggregationType.TICK:
            return self.current_bar.tick_count >= agg_val
        elif agg_type == AggregationType.VOLUME:
            return self.current_bar.current_aggregated_volume >= agg_val
        # Add logic for RANGE and REVERSAL if needed
        return False

    def _create_new_bar(self, timestamp: datetime, price: float) -> None:
        """Initializes a new `current_bar` based on the first tick's data."""
        rounded_price = round(price / self.config.tick_size) * self.config.tick_size
        
        if self.config.aggregation_type == AggregationType.TIME:
            start_time = pd.Timestamp(timestamp).floor(str(self.config.aggregation_value)).to_pydatetime()
        else:
            start_time = timestamp

        self.current_bar = FootprintBar(
            start_time=start_time,
            end_time=timestamp,
            open_price=rounded_price,
            high_price=rounded_price,
            low_price=rounded_price,
            close_price=rounded_price,
        )
        logger.debug(f"Created new bar starting at {start_time}")

    def _finalize_current_bar(self) -> None:
        """Finalizes the current bar's stats and adds it to the historical list."""
        if self.current_bar is None:
            return

        self.current_bar.update_bar_statistics(self.config.value_area_percentage)
        self.bars.append(self.current_bar)
        
        if len(self.bars) > self.config.max_bars_in_memory:
            self.bars.pop(0)

        logger.debug(f"Finalized bar: {self.current_bar.start_time} - {self.current_bar.end_time}, "
                     f"Volume: {self.current_bar.total_bar_volume}, Delta: {self.current_bar.bar_delta}")
        self.current_bar = None

    def get_all_completed_bars(self) -> List[FootprintBar]:
        """Returns a copy of the list of all finalized bars."""
        return list(self.bars)