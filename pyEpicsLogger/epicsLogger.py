#!/usr/bin/env python3
"""
EPICS Logger - Multi-Channel EPICS Process Variable Logger

A command-line tool to monitor multiple EPICS PV channels and log all value changes with timestamps to CSV files.
"""

import time
import logging
import argparse
import sys
import signal
import csv
import os
from pathlib import Path
from typing import Optional, List, Dict
try:
    import coloredlogs
    HAS_COLOREDLOGS = True
except ImportError:
    HAS_COLOREDLOGS = False
    print("Warning: coloredlogs not available. Install with: pip install coloredlogs")

try:
    from epics import PV
    HAS_EPICS = True
except ImportError:
    HAS_EPICS = False
    print("Error: pyepics not available. Install with: pip install pyepics")
    sys.exit(1)

from datetime import datetime, timedelta


class EPICSLogger:
    """Multi-channel EPICS PV logger with configurable parameters."""
    
    def __init__(self, pv_list: List[str], clock_offset: float = 0.0,
                 verbose: bool = False, log_file: Optional[str] = None,
                 data_file: Optional[str] = None, channel_prefix: str = ""):
        """
        Initialize the EPICS Logger.
        
        Args:
            pv_list: List of EPICS PV names to monitor
            clock_offset: Clock offset adjustment in seconds
            verbose: Enable verbose logging
            log_file: Optional log file path
            data_file: Optional CSV file path to save channel data
            channel_prefix: Optional prefix to add to all channel names
        """
        self.pv_list = [f"{channel_prefix}{pv}" if channel_prefix else pv for pv in pv_list]
        self.clock_offset = clock_offset
        self.verbose = verbose
        self.log_file = log_file
        self.data_file = data_file
        self.channel_prefix = channel_prefix
        
        # State tracking
        self.pvs: Dict[str, PV] = {}
        self.pv_states: Dict[str, Dict] = {}
        self.change_count = 0
        self.start_time = None
        self.running = True
        
        # Dataset collection
        self.channel_data: List[Dict] = []
        self.csv_file_initialized = False
        self.csv_fieldnames = [
            'sequence_number',
            'pv_name',
            'pv_value',
            'pv_type',
            'epics_timestamp',
            'epics_datetime',
            'local_datetime',
            'clock_skew_seconds',
            'clock_offset_applied',
            'previous_value',
            'value_changed',
            'connection_status',
            'severity',
            'alarm_status'
        ]
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_csv_file(self):
        """Initialize the CSV file with headers."""
        if not self.data_file or self.csv_file_initialized:
            return
        
        try:
            with open(self.data_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
                writer.writeheader()
            
            self.csv_file_initialized = True
            self.logger.info(f"Initialized CSV dataset file: {self.data_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV file: {e}")
            self.data_file = None  # Disable data collection if file can't be created
    
    def _append_to_csv(self, record: Dict):
        """Append a single record to the CSV file immediately."""
        if not self.data_file or not self.csv_file_initialized:
            return
        
        try:
            with open(self.data_file, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
                writer.writerow(record)
                
        except Exception as e:
            self.logger.error(f"Failed to append to CSV file: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup colored logging with optional file output."""
        logger = logging.getLogger('epicslogger')
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Setup coloredlogs if available
        if HAS_COLOREDLOGS:
            # Configure coloredlogs with custom format
            coloredlogs.install(
                level=logging.DEBUG if self.verbose else logging.INFO,
                logger=logger,
                fmt='[%(asctime)s] [%(levelname)8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level_styles={
                    'debug': {'color': 'cyan'},
                    'info': {'color': 'green'},
                    'warning': {'color': 'yellow'},
                    'error': {'color': 'red'},
                    'critical': {'color': 'red', 'bold': True}
                }
            )
        else:
            # Fallback to standard logging
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler if specified
        if self.log_file:
            try:
                file_handler = logging.FileHandler(self.log_file)
                file_formatter = logging.Formatter(
                    '[%(asctime)s] [%(levelname)8s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
                logger.info(f"Logging to file: {self.log_file}")
            except Exception as e:
                logger.error(f"Failed to setup file logging: {e}")
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _on_change(self, pvname=None, value=None, timestamp=None, **kwargs):
        """Callback function for PV value changes."""
        try:
            # Convert EPICS timestamp to datetime, adjusted for offset
            epics_time = datetime.utcfromtimestamp(timestamp) + timedelta(seconds=self.clock_offset)
            local_time = datetime.utcnow()
            
            self.logger.debug(f"PV {pvname} changed to {value} at {epics_time.strftime('%H:%M:%S.%f')[:-3]}")
            
            # Get PV info for additional metadata
            pv_obj = self.pvs.get(pvname)
            pv_type = pv_obj.type if pv_obj else "UNKNOWN"
            connection_status = pv_obj.connected if pv_obj else False
            severity = getattr(pv_obj, 'severity', 0) if pv_obj else 0
            alarm_status = getattr(pv_obj, 'status', 0) if pv_obj else 0
            
            # Check for value changes
            previous_value = self.pv_states.get(pvname, {}).get('last_value')
            value_changed = previous_value is None or value != previous_value
            
            if value_changed:
                self.change_count += 1
                self.logger.info(f"Change #{self.change_count}: {pvname} = {value} (was {previous_value})")
                
                # Check for timestamp skew
                skew = (epics_time - local_time).total_seconds()
                if abs(skew) > 1.0:  # More than 1 second skew
                    self.logger.error(
                        f"Clock skew detected: EPICS timestamp {skew:+.3f}s relative to local time"
                    )
                elif abs(skew) > 0.5:  # More than 0.5 second skew
                    self.logger.warning(
                        f"Minor clock skew: EPICS timestamp {skew:+.3f}s relative to local time"
                    )
                elif self.verbose:
                    self.logger.debug(f"Clock skew: {skew:+.3f}s")
            
            # Collect comprehensive data for dataset
            channel_record = {
                'sequence_number': len(self.channel_data) + 1,
                'pv_name': pvname,
                'pv_value': value,
                'pv_type': pv_type,
                'epics_timestamp': timestamp,  # Raw EPICS timestamp
                'epics_datetime': epics_time.isoformat(),
                'local_datetime': local_time.isoformat(),
                'clock_skew_seconds': (epics_time - local_time).total_seconds(),
                'clock_offset_applied': self.clock_offset,
                'previous_value': previous_value,
                'value_changed': value_changed,
                'connection_status': connection_status,
                'severity': severity,
                'alarm_status': alarm_status
            }
            
            # Add to dataset
            self.channel_data.append(channel_record)
            
            # Immediately append to CSV file if enabled
            if self.data_file:
                self._append_to_csv(channel_record)
            
            # Update state
            if pvname not in self.pv_states:
                self.pv_states[pvname] = {}
            self.pv_states[pvname]['last_value'] = value
            self.pv_states[pvname]['last_timestamp'] = epics_time
            
        except Exception as e:
            self.logger.error(f"Error in callback for {pvname}: {e}")
    
    def _save_dataset(self):
        """Dataset is now continuously saved, this just reports the final statistics."""
        if not self.data_file or not self.channel_data:
            return
        
        try:
            self.logger.info(f"Dataset continuously saved to {self.data_file}")
            self.logger.info(f"Total records written: {len(self.channel_data)}")
            
        except Exception as e:
            self.logger.error(f"Error reporting dataset status: {e}")
    
    def _print_statistics(self):
        """Print monitoring statistics."""
        if self.start_time:
            duration = datetime.utcnow() - self.start_time
            self.logger.info(f"Monitoring duration: {duration}")
            self.logger.info(f"Total channel updates recorded: {len(self.channel_data)}")
            self.logger.info(f"Total value changes: {self.change_count}")
            self.logger.info(f"Monitored channels: {len(self.pv_list)}")
            
            # Per-channel statistics
            for pv_name in self.pv_list:
                pv_records = [r for r in self.channel_data if r['pv_name'] == pv_name]
                pv_changes = [r for r in pv_records if r['value_changed']]
                self.logger.info(f"  {pv_name}: {len(pv_records)} updates, {len(pv_changes)} changes")
            
            # Save dataset if file specified
            if self.data_file:
                self._save_dataset()
    
    def connect(self) -> bool:
        """Connect to all EPICS PVs."""
        try:
            self.logger.info(f"Connecting to {len(self.pv_list)} PV(s):")
            for pv_name in self.pv_list:
                self.logger.info(f"  - {pv_name}")
            
            # Create PV objects
            for pv_name in self.pv_list:
                try:
                    pv = PV(pv_name)
                    self.pvs[pv_name] = pv
                    
                    # Wait for connection
                    if not pv.wait_for_connection(timeout=10.0):
                        self.logger.error(f"Failed to connect to PV {pv_name} within 10 seconds")
                        return False
                    
                    self.logger.info(f"Connected to {pv_name}: {pv.value} (type: {pv.type})")
                    
                    # Add callback
                    pv.add_callback(self._on_change)
                    
                    # Initialize state
                    self.pv_states[pv_name] = {
                        'last_value': pv.value,
                        'last_timestamp': datetime.utcnow()
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error connecting to PV {pv_name}: {e}")
                    return False
            
            self.logger.info(f"Successfully connected to all {len(self.pvs)} PV(s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during connection setup: {e}")
            return False
    
    def run(self):
        """Main monitoring loop."""
        self.logger.info(f"Starting EPICS logger for {len(self.pv_list)} channel(s)")
        for pv_name in self.pv_list:
            self.logger.info(f"  - {pv_name}")
        self.logger.info(f"Clock offset: {self.clock_offset:.1f}s")
        if self.data_file:
            self.logger.info(f"Dataset will be saved to: {self.data_file}")
        else:
            self.logger.info("No dataset file specified - data will not be saved")
        
        if not self.connect():
            return False
        
        # Initialize CSV file if data collection is enabled
        if self.data_file:
            self._initialize_csv_file()
        
        self.start_time = datetime.utcnow()
        
        try:
            # Status update interval
            last_status = time.time()
            status_interval = 60  # seconds
            
            while self.running:
                time.sleep(0.1)  # Short sleep to be responsive to signals
                
                # Periodic status updates
                if time.time() - last_status > status_interval:
                    status_msg = (
                        f"Status: {len(self.channel_data)} updates recorded, "
                        f"{self.change_count} value changes across {len(self.pv_list)} channels"
                    )
                    if self.data_file and self.csv_file_initialized:
                        status_msg += f" (saved to {self.data_file})"
                    self.logger.info(status_msg)
                    last_status = time.time()
                    
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            self._print_statistics()
            for pv in self.pvs.values():
                if pv:
                    pv.clear_callbacks()
            self.logger.info("Monitoring stopped")
        
        return True


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Monitor multiple EPICS PV channels and log all value changes with timestamps",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Channel specification options
    parser.add_argument(
        'pv_names',
        nargs='*',
        help="EPICS Process Variable names to monitor (space-separated)"
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        help="File containing list of PV names (one per line)"
    )
    
    parser.add_argument(
        '-p', '--prefix',
        type=str,
        default="",
        help="Prefix to add to all channel names"
    )
    
    parser.add_argument(
        '-o', '--offset',
        type=float,
        default=0.0,
        help="Clock offset adjustment in seconds"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose logging (DEBUG level)"
    )
    
    parser.add_argument(
        '-l', '--log-file',
        type=str,
        help="Log to file in addition to console"
    )
    
    parser.add_argument(
        '-d', '--data-file',
        type=str,
        help="Save channel data to CSV file"
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Determine PV list - validate that exactly one method is provided
    pv_list = []
    if args.file and args.pv_names:
        print("Error: Cannot specify both PV names and --file option", file=sys.stderr)
        sys.exit(1)
    elif args.file:
        # Read PVs from file
        try:
            with open(args.file, 'r') as f:
                pv_list = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            print(f"Loaded {len(pv_list)} PV names from {args.file}")
        except Exception as e:
            print(f"Error reading PV file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.pv_names:
        # Use command line PVs
        pv_list = args.pv_names
    else:
        # Neither provided
        print("Error: Either specify PV names or use --file option", file=sys.stderr)
        print("Examples:")
        print("  python3 epicsLogger.py PV1 PV2 PV3")
        print("  python3 epicsLogger.py --file pvs.txt")
        sys.exit(1)
    
    if not pv_list:
        print("Error: No PV names specified", file=sys.stderr)
        sys.exit(1)
    
    # Process data file path - default to data directory if relative path
    data_file = args.data_file
    if data_file and not os.path.isabs(data_file):
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        data_file = str(data_dir / data_file)
    
    # Create and run logger
    logger = EPICSLogger(
        pv_list=pv_list,
        clock_offset=args.offset,
        verbose=args.verbose,
        log_file=args.log_file,
        data_file=data_file,
        channel_prefix=args.prefix
    )
    
    success = logger.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
