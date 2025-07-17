# pyEpicsLogger - Multi-Channel EPICS Process Variable Logger

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-jacotay7%2FpyEpicsLogger-blue)](https://github.com/jacotay7/pyEpicsLogger)

A powerful command-line tool for monitoring multiple EPICS Process Variable channels and logging all value changes with timestamps to CSV files. Designed for scientific data acquisition and instrumentation monitoring.

## Features

- **Multi-channel monitoring** - Monitor multiple EPICS PVs simultaneously
- **Comprehensive logging** - Log all value changes with detailed timestamps
- **CSV data export** - Export all data to CSV files in the `data/` directory
- **Command-line interface** with configurable parameters
- **Colored logging** with different levels (INFO, WARNING, ERROR, DEBUG)
- **Verbose mode** for detailed debugging
- **File logging** option for persistent logs
- **Statistics tracking** with per-channel analytics
- **Signal handling** for graceful shutdown (Ctrl+C)
- **Clock skew detection** between EPICS and local time
- **Connection timeout** and error handling
- **Periodic status updates** during monitoring
- **Flexible PV specification** - Command line arguments or file input
- **Package installation** - Install as a Python package with entry points

## Installation

### Option 1: Install as Package (Recommended)
```bash
# Clone the repository
git clone https://github.com/jacotay7/pyEpicsLogger.git
cd pyEpicsLogger

# Install the package
pip install -e .

# Now you can use the command anywhere
pyepicslogger "YOUR:PV:NAME"
```

### Option 2: Direct Usage
```bash
# Clone the repository
git clone https://github.com/jacotay7/pyEpicsLogger.git
cd pyEpicsLogger

# Install dependencies
pip install -r requirements.txt

# Run directly
python3 pyEpicsLogger/epicsLogger.py "YOUR:PV:NAME"
```

## Quick Start

After installation, you can use the logger in several ways:

```bash
# Monitor single PV (saves to data/ directory by default)
pyepicslogger "DEVICE:TEMPERATURE"

# Monitor multiple PVs with data logging
pyepicslogger "PV1" "PV2" "PV3" --data-file measurements.csv --verbose

# Monitor PVs from a file
echo -e "DEVICE:TEMP\nDEVICE:PRESSURE" > pvs.txt
pyepicslogger --file pvs.txt --data-file experiment_data.csv
```

## Usage

### Basic Commands
```bash
# Monitor single PV
pyepicslogger "your:pv:name"

# Monitor multiple PVs
pyepicslogger "pv1:name" "pv2:name" "pv3:name"

# Alternative command name
epicslogger "your:pv:name"
```

### Using PV List Files
Create a text file with PV names (one per line):
```bash
# pvs.txt
DEVICE:TEMPERATURE
DEVICE:PRESSURE
DEVICE:FLOW_RATE
DEVICE:STATUS
```

Then run:
```bash
pyepicslogger --file pvs.txt
```

### Advanced Usage
```bash
# Monitor with data logging (saves to data/measurements.csv)
pyepicslogger "pv1" "pv2" --data-file measurements.csv

# Add prefix to all PV names
pyepicslogger --file pvs.txt --prefix "LAB:SYSTEM:"

# Enable verbose logging
pyepicslogger "pv1" "pv2" --verbose

# Log to file
pyepicslogger "pv1" "pv2" --log-file logger.log

# Adjust for clock offset
pyepicslogger "pv1" "pv2" --offset -0.1

# Combined options
pyepicslogger --file pvs.txt \
    --prefix "LAB:" \
    --offset 0.0 \
    --verbose \
    --log-file logs/epics_logger.log \
    --data-file experiment_$(date +%Y%m%d).csv
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `pv_names` | - | EPICS Process Variable names to monitor | Required* |
| `--file` | `-f` | File containing list of PV names (one per line) | None |
| `--prefix` | `-p` | Prefix to add to all channel names | "" |
| `--offset` | `-o` | Clock offset adjustment (seconds) | 0.0 |
| `--verbose` | `-v` | Enable verbose logging (DEBUG level) | False |
| `--log-file` | `-l` | Log to file in addition to console | None |
| `--data-file` | `-d` | Save channel data to CSV file (in `data/` if relative path) | None |
| `--version` | - | Show version and exit | - |
| `--help` | `-h` | Show help message and exit | - |

*Either `pv_names` or `--file` is required

## Data Storage

All CSV data files are automatically saved to the `data/` directory when using relative paths:

- `--data-file measurements.csv` → saves to `data/measurements.csv`
- `--data-file /absolute/path/data.csv` → saves to exact path specified
- The `data/` directory is created automatically if it doesn't exist
## CSV Data Format

When using `--data-file`, the logger saves comprehensive data about each PV update in the `data/` directory:

| Column | Description |
|--------|-------------|
| `sequence_number` | Sequential record number |
| `pv_name` | EPICS PV name |
| `pv_value` | PV value at time of change |
| `pv_type` | EPICS data type |
| `epics_timestamp` | Raw EPICS timestamp |
| `epics_datetime` | Human-readable EPICS datetime |
| `local_datetime` | Local system datetime |
| `clock_skew_seconds` | Time difference between EPICS and local |
| `clock_offset_applied` | Applied clock offset |
| `previous_value` | Previous PV value |
| `value_changed` | Boolean indicating if value changed |
| `connection_status` | PV connection status |
| `severity` | EPICS alarm severity |
| `alarm_status` | EPICS alarm status |

## Output Examples

The logger provides different types of log messages with colored output:

- **INFO** (Green): Normal channel updates and status information
- **WARNING** (Yellow): Minor clock skew and connection warnings
- **ERROR** (Red): Connection errors and significant clock skew
- **DEBUG** (Cyan): Detailed information (verbose mode only)

### Example Output
```
[2025-07-16 14:30:15] [    INFO] Starting EPICS logger for 3 channel(s)
[2025-07-16 14:30:15] [    INFO]   - LAB:TEMP:SENSOR1
[2025-07-16 14:30:15] [    INFO]   - LAB:PRESS:SENSOR2
[2025-07-16 14:30:15] [    INFO]   - LAB:FLOW:METER1
[2025-07-16 14:30:15] [    INFO] Clock offset: 0.0s
[2025-07-16 14:30:15] [    INFO] Dataset will be saved to: data/lab_data.csv
[2025-07-16 14:30:15] [    INFO] Connected to LAB:TEMP:SENSOR1: 23.5 (type: DBF_DOUBLE)
[2025-07-16 14:30:15] [    INFO] Connected to LAB:PRESS:SENSOR2: 1013.2 (type: DBF_DOUBLE)
[2025-07-16 14:30:15] [    INFO] Connected to LAB:FLOW:METER1: 15.2 (type: DBF_DOUBLE)
[2025-07-16 14:30:16] [    INFO] Change #1: LAB:TEMP:SENSOR1 = 23.6 (was 23.5)
[2025-07-16 14:30:17] [    INFO] Change #2: LAB:PRESS:SENSOR2 = 1013.4 (was 1013.2)
```

## Dependencies

### Core Requirements
- `pyepics>=3.5.2` - EPICS Channel Access for Python
- `coloredlogs>=15.0.1` - Colored terminal logging

### Optional Analysis Tools
- `pandas>=1.5.0` - Data analysis
- `matplotlib>=3.6.0` - Plotting
- `seaborn>=0.12.0` - Statistical visualization
- `plotly>=5.15.0` - Interactive plots
- `numpy>=1.24.0` - Numerical computing

### Testing Dependencies
- `softioc>=4.4.0` - For running test IOCs

## Signal Handling

The monitor handles shutdown signals gracefully:
- **Ctrl+C** (SIGINT): Graceful shutdown with statistics
- **SIGTERM**: Clean termination

## Statistics

When the logger shuts down, it displays:
- Total monitoring duration
- Number of channel updates recorded
- Number of value changes detected
- Number of monitored channels
- Per-channel update and change counts

## Development and Testing

### Testing with the Included Test IOC

A comprehensive test IOC is provided for testing the logger functionality:

```bash
# Start the test IOC (in one terminal)
cd test/
python3 test_ioc.py

# Test the logger (in another terminal)
pyepicslogger TEST:HEARTBEAT TEST:COUNTER --verbose --data-file test_run.csv
```

### Automated Testing
Use the provided test script for various scenarios:
```bash
cd test/
chmod +x test.sh
./test.sh
```

### Test Different Scenarios
```bash
# Test with file input
echo -e "TEST:HEARTBEAT\nTEST:COUNTER\nTEST:FREQUENCY" > test_pvs.txt
pyepicslogger --file test_pvs.txt --data-file test_data.csv

# Test with prefix
pyepicslogger HEARTBEAT COUNTER --prefix "TEST:" --verbose

# Test data logging with timestamp
pyepicslogger TEST:HEARTBEAT --data-file "heartbeat_$(date +%Y%m%d_%H%M%S).csv"
```

See [test/TEST_IOC.md](test/TEST_IOC.md) for detailed testing instructions.

## Project Structure

```
pyEpicsLogger/
├── pyEpicsLogger/          # Main package
│   └── epicsLogger.py      # Core logger implementation
├── data/                   # Default directory for CSV outputs
├── test/                   # Testing framework
│   ├── test_ioc.py        # Test IOC implementation
│   ├── test.sh            # Automated test script
│   ├── TEST_IOC.md        # Testing documentation
│   └── example_pvs.txt    # Example PV list
├── analysis/              # Data analysis tools
├── setup.py              # Package installation
├── requirements.txt      # Dependencies
├── README.md            # This file
└── LICENSE              # License information
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Connection Issues
- Verify the PV name is correct using `caget PV_NAME`
- Check EPICS environment variables (`EPICS_CA_ADDR_LIST`, etc.)
- Ensure the IOC is running and accessible
- Check firewall settings for EPICS Channel Access ports

### Installation Issues
- Ensure Python 3.8+ is installed
- Install missing dependencies: `pip install -r requirements.txt`
- For package installation: `pip install -e .`
- Verify Python environment has access to installed packages

### Permission Issues
- Ensure write permissions for the `data/` directory
- Check write permissions for log files

### Import Errors
```bash
# If pyepics is not found
pip install pyepics

# If coloredlogs is not found (optional)
pip install coloredlogs

# Install all dependencies
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Jacob Taylor**
- GitHub: [@jacotay7](https://github.com/jacotay7)
- Email: jtaylor@keck.hawaii.edu

## Acknowledgments

- Built for scientific instrumentation at W. M. Keck Observatory
- Uses the [pyepics](https://pyepics.github.io/pyepics/) library for EPICS Channel Access
- Inspired by the need for reliable multi-channel data logging in laboratory environments
