# footprint_analyzer/examples/run_aggregation_example.py

"""
run_aggregation_example.py: Demonstration of the FootprintEngine

This script shows how to import and use the FootprintEngine to process
a simulated stream of tick data for both time-based and tick-based aggregation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# This allows the script to find the 'footprint_analyzer' package in the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary components from our library
from footprint_analyzer.config import FootprintEngineConfig
from footprint_analyzer.domain import AggregationType
from footprint_analyzer.engine import FootprintEngine

# --- Setup logging for the example ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FootprintExample")


def generate_tick_data(num_ticks: int, start_price: float, start_time: datetime) -> pd.DataFrame:
    """Generates a DataFrame of simulated tick data."""
    ticks = []
    current_price = start_price
    for i in range(num_ticks):
        price_change = np.random.choice([-0.25, 0.25, 0])
        current_price += price_change
        tick_timestamp = start_time + timedelta(seconds=i * 0.5 + np.random.uniform(-0.1, 0.1))
        
        ticks.append({
            'datetime': tick_timestamp,
            'price': current_price,
            'volume': np.random.randint(1, 50),
            'is_bid_trade': np.random.choice([True, False])
        })
    return pd.DataFrame(ticks)

def print_bar_summary(bar, bar_type: str):
    """Prints a formatted summary of a completed footprint bar."""
    logger.info(
        f"\n--- COMPLETED {bar_type.upper()} BAR ---\n"
        f"Time         : {bar.start_time.strftime('%H:%M:%S')} to {bar.end_time.strftime('%H:%M:%S')}\n"
        f"OHLC         : O={bar.open_price:.2f}, H={bar.high_price:.2f}, L={bar.low_price:.2f}, C={bar.close_price:.2f}\n"
        f"Volume       : {bar.total_bar_volume} (B: {bar.total_bar_bid_volume} | A: {bar.total_bar_ask_volume})\n"
        f"Delta        : {bar.bar_delta}\n"
        f"POC          : {bar.poc_price:.2f} \n"
        f"Value Area   : {bar.value_area_low:.2f} to {bar.value_area_high:.2f}\n"
        f"Total Ticks  : {bar.tick_count}"
    )

if __name__ == "__main__":
    # --- Generate common data for both examples ---
    simulated_ticks = generate_tick_data(
        num_ticks=500,
        start_price=4500.00,
        start_time=datetime(2025, 8, 9, 9, 30, 0)
    )
    logger.info(f"Generated {len(simulated_ticks)} ticks for demonstration.")

    # --- 1. Time-Based Aggregation Example (1 Minute Bars) ---
    logger.info("\n\n--- RUNNING TIME-BASED AGGREGATION (1min) ---")
    config_time = FootprintEngineConfig(
        tick_size=0.25,
        aggregation_type=AggregationType.TIME,
        aggregation_value="1min"
    )
    engine_time = FootprintEngine(config_time)
    engine_time.process_tick_batch(simulated_ticks)
    
    # Finalize the last bar since the data stream has ended
    if engine_time.current_bar:
        engine_time._finalize_current_bar()

    completed_time_bars = engine_time.get_all_completed_bars()
    logger.info(f"Time engine produced {len(completed_time_bars)} completed bars.")
    for bar in completed_time_bars:
        print_bar_summary(bar, "Time")

    # --- 2. Tick-Based Aggregation Example (100 Tick Bars) ---
    logger.info("\n\n--- RUNNING TICK-BASED AGGREGATION (100 ticks) ---")
    config_tick = FootprintEngineConfig(
        tick_size=0.25,
        aggregation_type=AggregationType.TICK,
        aggregation_value=100 # New bar every 100 ticks
    )
    engine_tick = FootprintEngine(config_tick)
    engine_tick.process_tick_batch(simulated_ticks)
    
    if engine_tick.current_bar:
        engine_tick._finalize_current_bar()
        
    completed_tick_bars = engine_tick.get_all_completed_bars()
    logger.info(f"Tick engine produced {len(completed_tick_bars)} completed bars.")
    for bar in completed_tick_bars:
        print_bar_summary(bar, "Tick")