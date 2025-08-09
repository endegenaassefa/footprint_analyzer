"""
domain.py: Core Data Models and Enumerations

This module contains the fundamental data structures that represent the building
blocks of the footprint chart, such as the individual price levels, the bars
themselves, and the various enumerations that define behavior.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Literal

# --- Enumerations for Configuration and Behavior ---

class BackgroundType(Enum):
    """Defines types of background rendering for footprint columns. (Sierra Chart mapping)"""
    NONE = 0
    FULL_BACKGROUND = 1
    VOLUME_PROFILE = 2
    # ... Add other enum members as needed

class ColoringMethod(Enum):
    """Defines methods for coloring backgrounds and text. (Sierra Chart mapping)"""
    NONE = 0
    BASED_ON_VOLUME_PERCENTAGE = 1
    BASED_ON_DOMINANT_SIDE_ASK_BID_VOL_PERCENTAGE = 6
    BASED_ON_DIAGONAL_DOMINANT_SIDE_ASK_BID_VOL_PERCENTAGE = 7
    BASED_ON_ASK_BID_VOL_DIFFERENCE_ACTUAL = 14
    # ... Add other enum members as needed

class NumberBarsTextType(Enum):
    """Defines the type of text displayed in footprint cells. (Sierra Chart mapping)"""
    NO_TEXT = 0
    ASK_VOL_BID_VOL_DIFFERENCE = 1
    VOLUME = 2
    BID_VOL_X_ASK_VOL = 4
    # ... Add other enum members as needed

class CandlestickMarkerStyle(Enum):
    """Defines styles for marking Open and Close prices. (Sierra Chart mapping)"""
    NONE = 0
    CANDLESTICK_OUTLINE = 6
    # ... Add other enum members as needed

class AggregationType(Enum):
    """Defines the method for aggregating ticks into a new bar."""
    TIME = "time"
    TICK = "tick"
    VOLUME = "volume"
    RANGE = "range"
    REVERSAL = "reversal"

# --- Core Data Models ---

@dataclass
class PriceLevelData:
    """Holds aggregated trading data for a single price level within a FootprintBar."""
    price: float
    bid_volume: int = 0
    ask_volume: int = 0
    bid_trades: int = 0
    ask_trades: int = 0

    # These fields are automatically calculated after initialization or update.
    total_volume: int = field(init=False)
    total_trades: int = field(init=False)
    delta: int = field(init=False)
    is_ask_dominant: bool = field(init=False)
    dominance_ratio: float = field(init=False)

    def __post_init__(self):
        """Initial calculation of derived metrics when the object is created."""
        self.update_derived_metrics()

    def update_derived_metrics(self, zero_handling: Literal["set_to_one", "inf"] = "set_to_one") -> None:
        """Recalculates derived metrics like total volume, delta, and ratios."""
        self.total_volume = self.bid_volume + self.ask_volume
        self.total_trades = self.bid_trades + self.ask_trades
        self.delta = self.ask_volume - self.bid_volume
        self.is_ask_dominant = self.ask_volume >= self.bid_volume

        numerator = self.ask_volume if self.is_ask_dominant else self.bid_volume
        denominator = self.bid_volume if self.is_ask_dominant else self.ask_volume

        if denominator == 0:
            if zero_handling == "set_to_one":
                denominator = 1  # As per Sierra Chart's "Enable Bid/Ask Ratios with Zeros as Ones"
            
            if denominator == 0: # Still zero if numerator was also 0 or handling is 'inf'
                self.dominance_ratio = float('inf') if numerator > 0 else 0.0
                return

        self.dominance_ratio = numerator / denominator

@dataclass
class FootprintBar:
    """Represents a single, complete footprint bar with all its associated metrics."""
    start_time: datetime
    end_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    price_levels: Dict[float, PriceLevelData] = field(default_factory=dict)

    # Bar-level summary statistics
    total_bar_volume: int = 0
    total_bar_ask_volume: int = 0
    total_bar_bid_volume: int = 0
    total_bar_trades: int = 0
    bar_delta: int = 0
    poc_price: Optional[float] = None
    value_area_high: Optional[float] = None
    value_area_low: Optional[float] = None
    is_up_bar: bool = False
    
    # Attributes for aggregation logic
    tick_count: int = 0
    current_aggregated_volume: int = 0
    bar_direction: int = 0  # 0=undetermined, 1=up, -1=down (for Reversal/Range)
    extreme_price_during_formation: Optional[float] = None

    def update_bar_statistics(self, value_area_percentage: float = 0.70) -> None:
        """
        Recalculates all bar-level summary statistics, including Point of Control (POC)
        and Value Area (VA), based on the current price_levels.
        """
        if not self.price_levels:
            self.is_up_bar = self.close_price >= self.open_price
            return

        # Reset and sum totals from price levels
        self.total_bar_volume = sum(level.total_volume for level in self.price_levels.values())
        self.total_bar_ask_volume = sum(level.ask_volume for level in self.price_levels.values())
        self.total_bar_bid_volume = sum(level.bid_volume for level in self.price_levels.values())
        self.total_bar_trades = sum(level.total_trades for level in self.price_levels.values())
        self.bar_delta = self.total_bar_ask_volume - self.total_bar_bid_volume
        self.is_up_bar = self.close_price >= self.open_price

        # Find Point of Control (POC)
        poc_level = max(self.price_levels.values(), key=lambda level: level.total_volume, default=None)
        if poc_level:
            self.poc_price = poc_level.price

        # Calculate Value Area (VA)
        if self.poc_price is not None and self.total_bar_volume > 0:
            target_va_volume = self.total_bar_volume * value_area_percentage
            sorted_prices = sorted(self.price_levels.keys())
            
            poc_index = sorted_prices.index(self.poc_price)
            va_volume = self.price_levels[self.poc_price].total_volume
            low_idx, high_idx = poc_index, poc_index

            while va_volume < target_va_volume:
                vol_above = self.price_levels[sorted_prices[high_idx + 1]].total_volume if high_idx + 1 < len(sorted_prices) else 0
                vol_below = self.price_levels[sorted_prices[low_idx - 1]].total_volume if low_idx - 1 >= 0 else 0

                if vol_above == 0 and vol_below == 0:
                    break  # Cannot expand further

                if vol_above >= vol_below:
                    high_idx += 1
                    va_volume += vol_above
                else:
                    low_idx -= 1
                    va_volume += vol_below
            
            self.value_area_high = sorted_prices[high_idx]
            self.value_area_low = sorted_prices[low_idx]