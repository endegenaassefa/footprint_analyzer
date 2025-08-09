"""
Footprint Analyzer Package

A professional Python library for processing financial tick data into footprint charts.
This package provides tools for aggregating market data and analyzing volume profiles
at each price level within time-based or tick-based bars.

Key Components:
- FootprintEngine: Main processing engine for tick data
- FootprintEngineConfig: Configuration settings
- FootprintBar: Data structure representing completed bars
- AggregationType: Enumeration for different aggregation methods
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Import main classes for easy access
from .engine import FootprintEngine
from .config import FootprintEngineConfig
from .domain import (
    FootprintBar,
    PriceLevelData,
    AggregationType,
    BackgroundType,
    ColoringMethod,
    NumberBarsTextType,
    CandlestickMarkerStyle
)

# Define what gets imported with "from footprint_analyzer import *"
__all__ = [
    "FootprintEngine",
    "FootprintEngineConfig", 
    "FootprintBar",
    "PriceLevelData",
    "AggregationType",
    "BackgroundType",
    "ColoringMethod", 
    "NumberBarsTextType",
    "CandlestickMarkerStyle"
]