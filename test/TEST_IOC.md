# Test IOC Instructions for pyEpicsLogger

## Quick Start

1. **Start the Test IOC:**
```bash
cd test/
python3 test_ioc.py
```

2. **In another terminal, test the logger:**
```bash
# If installed as package
pyepicslogger TEST:HEARTBEAT --verbose

# If running from source
python3 pyEpicsLogger/epicsLogger.py TEST:HEARTBEAT --verbose

# Legacy compatibility (pvMonitor.py still works)
python3 pvMonitor.py TEST:HEARTBEAT --verbose
```

## IOC Features

The test IOC provides these PVs:
- `TEST:HEARTBEAT` - Toggles between 0 and 1 at 1Hz
- `TEST:COUNTER` - Counts the number of transitions
- `TEST:STATUS` - IOC status (0=STOPPED, 1=RUNNING)
- `TEST:FREQUENCY` - Adjustable frequency (0.1-10.0 Hz)
- `TEST:TEMPERATURE` - Simulated temperature sensor with noise
- `TEST:PRESSURE` - Simulated pressure sensor
- `TEST:FLOW` - Simulated flow meter
- `TEST:ALARM` - Test alarm state changes

## Testing Different Scenarios

### Test Normal Operation
```bash
# Terminal 1: Start IOC
cd test/
python3 test_ioc.py

# Terminal 2: Monitor with default settings (1Hz ± 0.2s)
pyepicslogger TEST:HEARTBEAT --verbose
```

### Test Multi-Channel Logging with Data Export
```bash
# Monitor multiple channels and save to data directory
pyepicslogger TEST:HEARTBEAT TEST:COUNTER TEST:TEMPERATURE \
    --data-file "test_run_$(date +%Y%m%d_%H%M%S).csv" \
    --verbose

# The CSV file will be automatically saved to data/
```

### Test Timing Anomalies
```bash
# Change frequency to 2 Hz
caput TEST:FREQUENCY 2.0

# Monitor expecting 1Hz (will show timing anomalies if using pvMonitor)
python3 pvMonitor.py TEST:HEARTBEAT --period 1.0 --tolerance 0.2 --verbose

# Monitor multiple channels with pyEpicsLogger
pyepicslogger TEST:HEARTBEAT TEST:COUNTER --verbose
```

### Test with Custom Device Name
```bash
# Start IOC with custom device name
python3 test_ioc.py --device MYTEST

# Monitor the custom PV
pyepicslogger MYTEST:HEARTBEAT --verbose
```

### Test with Different Initial Frequency
```bash
# Start IOC at 0.5 Hz
python3 test_ioc.py --frequency 0.5

# Monitor with pyEpicsLogger
pyepicslogger TEST:HEARTBEAT --verbose --data-file "slow_heartbeat.csv"
```

### Test File Input Method
```bash
# Create a PV list file
echo -e "TEST:HEARTBEAT\nTEST:TEMPERATURE\nTEST:PRESSURE\nTEST:FLOW" > test_pvs.txt

# Monitor using file input
pyepicslogger --file test_pvs.txt --data-file "multi_channel_test.csv" --verbose
```
## Using the Test Script

For automated testing, use the provided test script:
```bash
cd test/
chmod +x test.sh
./test.sh
```

This provides a menu-driven interface for various test scenarios including:
- Starting the IOC
- Running multi-channel tests  
- Testing data logging to CSV files
- Testing file input methods
- Frequency change testing

## Package vs Direct Usage

### Using Installed Package (Recommended)
```bash
# Install package first
pip install -e .

# Use the command anywhere
pyepicslogger TEST:HEARTBEAT TEST:COUNTER --verbose --data-file test.csv
```

### Direct Script Usage
```bash
# From repository root
python3 pyEpicsLogger/epicsLogger.py TEST:HEARTBEAT --verbose

# Legacy pvMonitor.py (still works for backward compatibility)
python3 pvMonitor.py TEST:HEARTBEAT --verbose
```

## Manual EPICS Commands

If you have EPICS tools installed:

```bash
# Check current values
caget TEST:HEARTBEAT TEST:COUNTER TEST:STATUS TEST:FREQUENCY

# Monitor continuously  
camonitor TEST:HEARTBEAT

# Change frequency
caput TEST:FREQUENCY 2.0

# Stop/start heartbeat
caput TEST:STATUS 0  # Stop
caput TEST:STATUS 1  # Start

# Monitor all test PVs
camonitor TEST:HEARTBEAT TEST:COUNTER TEST:TEMPERATURE TEST:PRESSURE
```

## Data Output Testing

### CSV File Creation
```bash
# Test automatic data directory creation
pyepicslogger TEST:HEARTBEAT TEST:TEMPERATURE \
    --data-file "experiment_$(date +%Y%m%d_%H%M%S).csv" \
    --verbose

# Check that file was created in data/ directory
ls -la data/
```

### Log File Testing
```bash
# Test log file creation
pyepicslogger TEST:HEARTBEAT --log-file "test.log" --verbose

# Test both data and log files
pyepicslogger TEST:HEARTBEAT TEST:COUNTER \
    --data-file "test_data.csv" \
    --log-file "test.log" \
    --verbose
```

## Performance Testing

### High-Frequency Testing
```bash
# Set IOC to maximum frequency
caput TEST:FREQUENCY 10.0

# Monitor high-frequency changes
pyepicslogger TEST:HEARTBEAT --verbose --data-file "high_freq_test.csv"
```

### Multi-Channel Load Testing
```bash
# Monitor all available test PVs
pyepicslogger TEST:HEARTBEAT TEST:COUNTER TEST:TEMPERATURE \
    TEST:PRESSURE TEST:FLOW TEST:ALARM \
    --data-file "load_test.csv" --verbose
```

## Troubleshooting

**IOC won't start:**
- Check if softioc is installed: `pip install softioc`
- Verify no other IOC is using the same PV names
- Check for port conflicts

**Logger can't connect:**
- Ensure IOC is running first
- Check PV name spelling  
- Verify EPICS environment variables if needed
- Try: `caget TEST:HEARTBEAT` to test basic connectivity

**Package command not found:**
- Install the package: `pip install -e .`
- Check if `~/.local/bin` is in your PATH
- Use absolute path: `python3 -m pyEpicsLogger.epicsLogger`

**Data files not in data/ directory:**
- Check if you're using absolute paths
- Verify write permissions in current directory
- Check if data/ directory was created: `ls -la data/`

**No timing anomalies detected (pvMonitor.py):**
- Try changing the IOC frequency: `caput TEST:FREQUENCY 2.0`
- Use stricter tolerance: `--tolerance 0.1`
- Monitor with wrong expected period to force anomalies

## Advanced Testing Scenarios

### Clock Offset Testing
```bash
# Test with clock offset
pyepicslogger TEST:HEARTBEAT --offset 0.1 --verbose --data-file "offset_test.csv"
```

### Prefix Testing  
```bash
# Test PV prefix functionality
pyepicslogger HEARTBEAT COUNTER --prefix "TEST:" --verbose
```

### Error Condition Testing
```bash
# Test with non-existent PV (should show connection errors)
pyepicslogger TEST:NONEXISTENT --verbose

# Test mixed valid/invalid PVs
pyepicslogger TEST:HEARTBEAT TEST:INVALID TEST:COUNTER --verbose
```

For more detailed testing procedures and troubleshooting, see the main [README.md](../README.md).
