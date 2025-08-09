# Footprint Analyzer

A professional Python library for processing financial tick data into footprint charts. This package provides tools for aggregating market data and analyzing volume profiles at each price level within time-based or tick-based bars.

## Features

- **Multiple Aggregation Types**: Support for time-based, tick-based, volume-based, range-based, and reversal-based aggregations
- **Volume Profile Analysis**: Detailed analysis of bid/ask volumes at each price level
- **Configurable Processing**: Flexible configuration system for different trading scenarios  
- **Professional Structure**: Clean, modular codebase following Python best practices
- **Type Safety**: Full type annotations for better IDE support and code reliability

## Installation

### From Source (Development)

1. Clone this repository:
```bash
git clone https://github.com/yourusername/footprint-analyzer.git
cd footprint-analyzer
```

2. Install in editable mode:
```bash
pip install -e .
```

### Dependencies

- Python 3.8+
- pandas >= 1.3.0
- numpy >= 1.20.0

## Quick Start

```python
from footprint_analyzer import FootprintEngine, FootprintEngineConfig, AggregationType
from datetime import datetime

# Configure the engine
config = FootprintEngineConfig(
    tick_size=0.25,
    aggregation_type=AggregationType.TIME,
    aggregation_value="1min"
)

# Initialize the engine
engine = FootprintEngine(config)

# Process tick data
engine.process_tick(
    timestamp=datetime.now(),
    price=4150.25,
    volume=10,
    is_bid_trade=True
)

# Get completed bars
bars = engine.get_bars()
```

## Configuration Options

The `FootprintEngineConfig` class provides extensive configuration options:

- **tick_size**: Minimum price movement (default: 0.25)
- **aggregation_type**: How to group ticks into bars (TIME, TICK, VOLUME, RANGE, REVERSAL)
- **aggregation_value**: Value for aggregation (e.g., "1min" for time, 100 for tick count)
- **value_area_percentage**: Percentage for value area calculation (default: 0.70)
- **enable_bid_ask_ratios_with_zeros_as_ones**: Handle zero volume scenarios (default: True)

## Examples

See the `examples/` directory for comprehensive usage examples:

- `run_aggregation_example.py`: Demonstrates basic tick processing and bar generation

To run the example:
```bash
cd examples
python run_aggregation_example.py
```

## Project Structure

```
footprint_analyzer/
├── footprint_analyzer/        # Main package
│   ├── __init__.py           # Package initialization
│   ├── engine.py             # Core processing engine
│   ├── config.py             # Configuration classes
│   └── domain.py             # Data models and enums
├── examples/                 # Usage examples
│   └── run_aggregation_example.py
├── tests/                    # Unit tests
│   └── test_engine.py
├── pyproject.toml           # Package configuration
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black footprint_analyzer/ examples/ tests/
```

### Type Checking

```bash
mypy footprint_analyzer/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions, issues, or contributions, please open an issue on GitHub.