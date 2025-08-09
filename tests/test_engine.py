"""
test_engine.py: Unit Tests for the FootprintEngine

These tests verify the core functionality of the engine, ensuring that
bar aggregation and metric calculations are correct under various conditions.
"""

import pandas as pd
from datetime import datetime, timedelta
import pytest

# Adjust path to import from the library
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from footprint_analyzer.config import FootprintEngineConfig
from footprint_analyzer.domain import AggregationType
from footprint_analyzer.engine import FootprintEngine

@pytest.fixture
def tick_data_1min():
    """Provides a DataFrame of ticks that spans just over 1 minute."""
    start_time = datetime(2025, 8, 9, 10, 0, 0)
    data = [
        # Ticks within the first minute
        {'datetime': start_time, 'price': 100.00, 'volume': 10, 'is_bid_trade': False}, # Ask
        {'datetime': start_time + timedelta(seconds=10), 'price': 100.25, 'volume': 5, 'is_bid_trade': True}, # Bid
        {'datetime': start_time + timedelta(seconds=59), 'price': 100.00, 'volume': 8, 'is_bid_trade': False}, # Ask
        # Tick that starts the next bar
        {'datetime': start_time + timedelta(seconds=61), 'price': 101.00, 'volume': 20, 'is_bid_trade': False},
    ]
    return pd.DataFrame(data)

def test_time_aggregation_bar_creation(tick_data_1min):
    """Verify that a 1-minute bar is finalized when the time boundary is crossed."""
    config = FootprintEngineConfig(aggregation_type=AggregationType.TIME, aggregation_value="1min", tick_size=0.25)
    engine = FootprintEngine(config)
    
    engine.process_tick_batch(tick_data_1min)
    
    completed_bars = engine.get_all_completed_bars()
    assert len(completed_bars) == 1, "Should have created exactly one completed bar."
    
    bar1 = completed_bars[0]
    assert bar1.open_price == 100.00
    assert bar1.high_price == 100.25
    assert bar1.low_price == 100.00
    assert bar1.close_price == 100.00
    assert bar1.start_time == datetime(2025, 8, 9, 10, 0, 0)
    
    # Check current (incomplete) bar
    assert engine.current_bar is not None
    assert engine.current_bar.open_price == 101.00

def test_bar_metrics_calculation(tick_data_1min):
    """Verify that volume, delta, and trades are calculated correctly."""
    config = FootprintEngineConfig(aggregation_type=AggregationType.TIME, aggregation_value="1min", tick_size=0.25)
    engine = FootprintEngine(config)
    
    engine.process_tick_batch(tick_data_1min)
    
    bar1 = engine.get_all_completed_bars()[0]
    
    assert bar1.total_bar_volume == 10 + 5 + 8
    assert bar1.total_bar_ask_volume == 10 + 8
    assert bar1.total_bar_bid_volume == 5
    assert bar1.bar_delta == (10 + 8) - 5
    assert len(bar1.price_levels) == 2

def test_tick_aggregation():
    """Verify that a 3-tick bar is created correctly."""
    config = FootprintEngineConfig(aggregation_type=AggregationType.TICK, aggregation_value=3, tick_size=0.25)
    engine = FootprintEngine(config)
    
    ticks = pd.DataFrame([
        {'datetime': datetime.now(), 'price': 100, 'volume': 1, 'is_bid_trade': True},
        {'datetime': datetime.now(), 'price': 100, 'volume': 1, 'is_bid_trade': True},
        {'datetime': datetime.now(), 'price': 100, 'volume': 1, 'is_bid_trade': True}, # Bar should complete here
        {'datetime': datetime.now(), 'price': 101, 'volume': 1, 'is_bid_trade': True},
    ])
    
    engine.process_tick_batch(ticks)
    
    completed_bars = engine.get_all_completed_bars()
    assert len(completed_bars) == 1
    assert completed_bars[0].tick_count == 3
    assert engine.current_bar.tick_count == 1