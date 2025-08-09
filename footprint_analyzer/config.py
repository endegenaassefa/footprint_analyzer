"""
config.py: Engine Configuration

This module defines the configuration object for the FootprintEngine.
Separating configuration from the core logic allows for easy adjustments
and different setups (e.g., for backtesting vs. live trading).
"""

from dataclasses import dataclass, field
from typing import List, Union, Literal

# Import from our local domain module
from .domain import AggregationType, NumberBarsTextType, CandlestickMarkerStyle

@dataclass
class FootprintEngineConfig:
    """Configuration settings for the FootprintEngine."""
    tick_size: float = 0.25
    aggregation_type: AggregationType = AggregationType.TIME
    
    # Value depends on aggregation_type:
    # TIME: "1min", "5H", etc.
    # TICK/VOLUME/RANGE/REVERSAL: integer
    aggregation_value: Union[str, int] = "1min"

    # Settings for how footprint data is calculated and presented
    value_area_percentage: float = 0.70
    enable_bid_ask_ratios_with_zeros_as_ones: bool = True
    
    # Engine operational settings
    max_bars_in_memory: int = 10000

    def get_zero_handling_for_ratios(self) -> Literal["set_to_one", "inf"]:
        """Helper to pass the correct ratio handling method based on config."""
        return "set_to_one" if self.enable_bid_ask_ratios_with_zeros_as_ones else "inf"