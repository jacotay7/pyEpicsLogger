#!/bin/bash

# Test script for pyEpicsLogger and IOC

echo "pyEpicsLogger Test Script"
echo "========================"
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if pyepicslogger package is installed
check_package_installed() {
    if command_exists pyepicslogger; then
        LOGGER_CMD="pyepicslogger"
        return 0
    elif [ -f "../pyEpicsLogger/epicsLogger.py" ]; then
        LOGGER_CMD="python3 ../pyEpicsLogger/epicsLogger.py"
        return 0
    elif [ -f "../pvMonitor.py" ]; then
        LOGGER_CMD="python3 ../pvMonitor.py"
        return 0
    else
        return 1
    fi
}

# Function to check if IOC is running
check_ioc() {
    if ! command_exists caget; then
        echo "Warning: EPICS tools not found. Install epics-base or similar package."
        return 1
    fi
    
    if caget TEST:HEARTBEAT >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start IOC in background
start_ioc() {
    echo "Starting test IOC..."
    python3 test_ioc.py &
    IOC_PID=$!
    echo "IOC started with PID: $IOC_PID"
    
    # Wait for IOC to start
    echo "Waiting for IOC to initialize..."
    sleep 3
    
    if check_ioc; then
        echo "✓ IOC is running and responsive"
        return 0
    else
        echo "✗ IOC failed to start or is not responsive"
        return 1
    fi
}

# Function to stop IOC
stop_ioc() {
    if [ ! -z "$IOC_PID" ]; then
        echo "Stopping IOC (PID: $IOC_PID)..."
        kill $IOC_PID 2>/dev/null
        wait $IOC_PID 2>/dev/null
        echo "IOC stopped"
    fi
}

# Function to run logger test
run_logger_test() {
    echo "Starting pyEpicsLogger test..."
    echo "Press Ctrl+C to stop the logger"
    echo "Using command: $LOGGER_CMD"
    echo
    $LOGGER_CMD TEST:HEARTBEAT TEST:TEMPERATURE TEST:PRESSURE --verbose
}

# Function to run single channel test
run_single_test() {
    echo "Starting single channel test..."
    echo "Press Ctrl+C to stop the logger"
    echo "Using command: $LOGGER_CMD"
    echo
    $LOGGER_CMD TEST:HEARTBEAT --verbose
}

# Function to run quick test
run_quick_test() {
    echo "Running quick test (10 seconds)..."
    echo "Using command: $LOGGER_CMD"
    timeout 10 $LOGGER_CMD TEST:HEARTBEAT TEST:COUNTER --verbose || true
    echo "Quick test completed"
}

# Function to run data logging test
run_data_test() {
    echo "Running data logging test (15 seconds)..."
    local data_file="test_data_$(date +%Y%m%d_%H%M%S).csv"
    echo "Data will be saved to: $data_file (in data/ directory if using relative path)"
    echo "Using command: $LOGGER_CMD"
    timeout 15 $LOGGER_CMD \
        TEST:HEARTBEAT TEST:TEMPERATURE TEST:PRESSURE TEST:FLOW TEST:ALARM \
        --data-file "$data_file" --verbose || true
    echo "Data logging test completed"
    
    # Check for data file in both current directory and data/ directory
    if [ -f "$data_file" ]; then
        echo "Data file created: $data_file"
        echo "Records written: $(tail -n +2 "$data_file" | wc -l)"
        echo "First few records:"
        head -n 5 "$data_file"
    elif [ -f "data/$data_file" ]; then
        echo "Data file created: data/$data_file"
        echo "Records written: $(tail -n +2 "data/$data_file" | wc -l)"
        echo "First few records:"
        head -n 5 "data/$data_file"
    elif [ -f "../data/$data_file" ]; then
        echo "Data file created: ../data/$data_file"
        echo "Records written: $(tail -n +2 "../data/$data_file" | wc -l)"
        echo "First few records:"
        head -n 5 "../data/$data_file"
    else
        echo "Warning: Data file not found in expected locations"
    fi
}

# Function to test file input
run_file_test() {
    echo "Testing file input method..."
    local pv_file="test_pvs.txt"
    echo "# Test PV List" > "$pv_file"
    echo "TEST:HEARTBEAT" >> "$pv_file"
    echo "TEST:TEMPERATURE" >> "$pv_file"
    echo "TEST:PRESSURE" >> "$pv_file"
    echo "TEST:FLOW" >> "$pv_file"
    
    echo "Created PV file: $pv_file"
    cat "$pv_file"
    echo
    echo "Running logger with file input (10 seconds)..."
    echo "Using command: $LOGGER_CMD"
    timeout 10 $LOGGER_CMD --file "$pv_file" --verbose || true
    echo "File test completed"
    rm -f "$pv_file"
}

# Trap to ensure cleanup
trap 'stop_ioc; exit' INT TERM EXIT

# Check what logger command to use
if ! check_package_installed; then
    echo "Error: Cannot find pyEpicsLogger!"
    echo "Please either:"
    echo "  1. Install the package: pip install -e ."
    echo "  2. Run from the repository root directory"
    echo "  3. Ensure pyEpicsLogger/epicsLogger.py or pvMonitor.py exists"
    exit 1
fi

echo "Detected logger command: $LOGGER_CMD"
echo

# Main menu
while true; do
    echo
    echo "pyEpicsLogger Test Options:"
    echo "1) Start IOC only"
    echo "2) Start IOC and run multi-channel logger (interactive)"
    echo "3) Start IOC and run single channel test (interactive)"  
    echo "4) Start IOC and run quick test (10 seconds)"
    echo "5) Start IOC and run data logging test (15 seconds)"
    echo "6) Start IOC and test file input method (10 seconds)"
    echo "7) Test with different frequency (2 Hz)"
    echo "8) Stop IOC"
    echo "9) Check IOC status"
    echo "10) Exit"
    echo
    read -p "Choose option [1-10]: " choice
    
    case $choice in
        1)
            start_ioc
            echo "IOC is running. You can now test manually with:"
            echo "  caget TEST:HEARTBEAT"
            echo "  camonitor TEST:HEARTBEAT"
            echo "  $LOGGER_CMD TEST:HEARTBEAT"
            echo "  $LOGGER_CMD TEST:HEARTBEAT TEST:TEMPERATURE TEST:PRESSURE"
            ;;
        2)
            if ! check_ioc; then
                start_ioc || continue
            fi
            run_logger_test
            ;;
        3)
            if ! check_ioc; then
                start_ioc || continue
            fi
            run_single_test
            ;;
        4)
            if ! check_ioc; then
                start_ioc || continue
            fi
            run_quick_test
            ;;
        5)
            if ! check_ioc; then
                start_ioc || continue
            fi
            run_data_test
            ;;
        6)
            if ! check_ioc; then
                start_ioc || continue
            fi
            run_file_test
            ;;
        7)
            if ! check_ioc; then
                start_ioc || continue
            fi
            echo "Changing frequency to 2 Hz..."
            if command_exists caput; then
                caput TEST:FREQUENCY 2.0
                echo "Running logger for 10 seconds at 2 Hz..."
                echo "Using command: $LOGGER_CMD"
                timeout 10 $LOGGER_CMD TEST:HEARTBEAT --verbose || true
                echo "Resetting frequency to 1 Hz..."
                caput TEST:FREQUENCY 1.0
            else
                echo "caput command not available"
            fi
            ;;
        8)
            stop_ioc
            IOC_PID=""
            ;;
        9)
            if check_ioc; then
                echo "✓ IOC is running"
                if command_exists caget; then
                    echo "Current values:"
                    caget TEST:HEARTBEAT TEST:COUNTER TEST:STATUS TEST:FREQUENCY TEST:TEMPERATURE
                fi
            else
                echo "✗ IOC is not running"
            fi
            ;;
        10)
            echo "Exiting..."
            break
            ;;
        *)
            echo "Invalid option. Please choose 1-10."
            ;;
    esac
done
