#!/usr/bin/env python3
"""
Simple EPICS IOC for testing the PV Monitor
Creates a 1Hz heartbeat PV that toggles between 0 and 1
Uses softioc library
"""

import time
import threading
import signal
import sys
from datetime import datetime

try:
    from softioc import softioc, builder
    HAS_SOFTIOC = True
except ImportError:
    HAS_SOFTIOC = False
    print("Error: softioc not available. Install with: pip install softioc")
    sys.exit(1)

class HeartbeatIOC:
    """Simple heartbeat IOC using softioc"""
    
    def __init__(self, device_name="TEST"):
        self.device_name = device_name
        self.running = True
        self.counter = 0
        self.heartbeat_state = 0
        self.frequency = 1.0  # Hz
        
        # Create PVs
        self._create_pvs()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] IOC initialized - Device: {device_name}")
    
    def _create_pvs(self):
        """Create the EPICS PVs"""
        # Set device name
        builder.SetDeviceName(self.device_name)
        
        # Heartbeat PV (toggles 0/1)
        self.heartbeat_pv = builder.aOut('HEARTBEAT', 
                                       initial_value=0,
                                       DESC="1Hz Heartbeat Signal")
        
        # Counter PV (counts transitions)
        self.counter_pv = builder.longOut('COUNTER',
                                        initial_value=0,
                                        DESC="Transition Counter")
        
        # Status PV (IOC status)
        self.status_pv = builder.mbbOut('STATUS',
                                      initial_value=1,
                                      PINI='YES',
                                      ZRST='STOPPED',
                                      ONST='RUNNING',
                                      TWST='ERROR',
                                      DESC="IOC Status")
        
        # Frequency control PV
        self.frequency_pv = builder.aOut('FREQUENCY',
                                       initial_value=1.0,
                                       EGU='Hz',
                                       PREC=2,
                                       DRVL=0.1,
                                       DRVH=10.0,
                                       DESC="Heartbeat Frequency",
                                       on_update=self._on_frequency_change)
        
        # Additional test PVs for general logging testing
        self.temperature_pv = builder.aOut('TEMPERATURE',
                                         initial_value=20.0,
                                         EGU='C',
                                         PREC=1,
                                         DESC="Simulated Temperature")
        
        self.pressure_pv = builder.aOut('PRESSURE',
                                      initial_value=1013.25,
                                      EGU='mbar',
                                      PREC=2,
                                      DESC="Simulated Pressure")
        
        self.flow_pv = builder.aOut('FLOW',
                                  initial_value=10.0,
                                  EGU='L/min',
                                  PREC=1,
                                  DESC="Simulated Flow Rate")
        
        self.alarm_pv = builder.mbbOut('ALARM',
                                     initial_value=0,
                                     PINI='YES',
                                     ZRST='NO_ALARM',
                                     ONST='MINOR',
                                     TWST='MAJOR',
                                     THST='INVALID',
                                     DESC="Alarm Status")
        
        # Build the IOC
        builder.LoadDatabase()
        softioc.iocInit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] PVs created:")
        print(f"  {self.device_name}:HEARTBEAT    - 1Hz toggle (0/1)")
        print(f"  {self.device_name}:COUNTER      - Transition counter")
        print(f"  {self.device_name}:STATUS       - IOC status")
        print(f"  {self.device_name}:FREQUENCY    - Heartbeat frequency")
        print(f"  {self.device_name}:TEMPERATURE  - Simulated temperature")
        print(f"  {self.device_name}:PRESSURE     - Simulated pressure")
        print(f"  {self.device_name}:FLOW         - Simulated flow rate")
        print(f"  {self.device_name}:ALARM        - Alarm status")
    
    def _on_frequency_change(self, new_value):
        """Handle frequency changes"""
        if 0.1 <= new_value <= 10.0:
            old_freq = self.frequency
            self.frequency = new_value
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Frequency changed: {old_freq:.2f} -> {new_value:.2f} Hz")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Invalid frequency: {new_value} (must be 0.1-10.0 Hz)")
            # Reset to previous value
            self.frequency_pv.set(self.frequency)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Received signal {signum}, shutting down...")
        self.running = False
    
    def _heartbeat_loop(self):
        """Main heartbeat generation loop"""
        last_time = time.time()
        last_simulation_time = time.time()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting heartbeat loop at {self.frequency} Hz")
        
        while self.running:
            current_time = time.time()
            
            # Calculate when next heartbeat should occur
            period = 1.0 / self.frequency
            if current_time - last_time >= period:
                # Toggle heartbeat
                self.heartbeat_state = 1 - self.heartbeat_state
                self.counter += 1
                
                # Update PVs
                self.heartbeat_pv.set(self.heartbeat_state)
                self.counter_pv.set(self.counter)
                
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                      f"Heartbeat: {self.heartbeat_state}, Count: {self.counter}")
                
                last_time = current_time
            
            # Update simulated values every 5 seconds
            if current_time - last_simulation_time >= 5.0:
                import random
                
                # Simulate temperature drift
                current_temp = self.temperature_pv.get()
                new_temp = current_temp + random.uniform(-0.5, 0.5)
                new_temp = max(15.0, min(30.0, new_temp))  # Keep between 15-30°C
                self.temperature_pv.set(new_temp)
                
                # Simulate pressure variations
                current_pressure = self.pressure_pv.get()
                new_pressure = current_pressure + random.uniform(-2.0, 2.0)
                new_pressure = max(1000.0, min(1030.0, new_pressure))  # Keep between 1000-1030 mbar
                self.pressure_pv.set(new_pressure)
                
                # Simulate flow rate changes
                current_flow = self.flow_pv.get()
                new_flow = current_flow + random.uniform(-1.0, 1.0)
                new_flow = max(5.0, min(20.0, new_flow))  # Keep between 5-20 L/min
                self.flow_pv.set(new_flow)
                
                # Occasionally trigger alarms
                if random.random() < 0.1:  # 10% chance
                    alarm_state = random.choice([0, 1, 2])  # NO_ALARM, MINOR, MAJOR
                    self.alarm_pv.set(alarm_state)
                    if alarm_state > 0:
                        alarm_names = ['NO_ALARM', 'MINOR', 'MAJOR']
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Alarm triggered: {alarm_names[alarm_state]}")
                
                last_simulation_time = current_time
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.01)
        
        # Set status to stopped
        self.status_pv.set(0)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat loop stopped")
    
    def run(self):
        """Start the IOC"""
        print("="*60)
        print("EPICS Test IOC - Multi-Channel Simulator (softioc)")
        print("="*60)
        print()
        print("Available PVs:")
        print(f"  {self.device_name}:HEARTBEAT    - 1Hz toggle (0/1)")
        print(f"  {self.device_name}:COUNTER      - Transition counter")
        print(f"  {self.device_name}:STATUS       - IOC status (0=STOPPED, 1=RUNNING)")
        print(f"  {self.device_name}:FREQUENCY    - Heartbeat frequency (0.1-10.0 Hz)")
        print(f"  {self.device_name}:TEMPERATURE  - Simulated temperature (15-30°C)")
        print(f"  {self.device_name}:PRESSURE     - Simulated pressure (1000-1030 mbar)")
        print(f"  {self.device_name}:FLOW         - Simulated flow rate (5-20 L/min)")
        print(f"  {self.device_name}:ALARM        - Alarm status (0=NO_ALARM, 1=MINOR, 2=MAJOR)")
        print()
        print("Control commands:")
        print(f"  caput {self.device_name}:FREQUENCY 2.0    # Change to 2 Hz")
        print(f"  caput {self.device_name}:STATUS 0         # Stop heartbeat")
        print(f"  caput {self.device_name}:STATUS 1         # Start heartbeat")
        print()
        print("Monitor commands:")
        print(f"  caget {self.device_name}:HEARTBEAT")
        print(f"  camonitor {self.device_name}:HEARTBEAT")
        print(f"  python3 epicsLogger.py {self.device_name}:HEARTBEAT")
        print(f"  python3 epicsLogger.py {self.device_name}:TEMPERATURE {self.device_name}:PRESSURE")
        print()
        print("Multi-channel test:")
        print(f"  python3 epicsLogger.py \\")
        print(f"    {self.device_name}:HEARTBEAT \\")
        print(f"    {self.device_name}:TEMPERATURE \\")
        print(f"    {self.device_name}:PRESSURE \\")
        print(f"    {self.device_name}:FLOW \\")
        print(f"    {self.device_name}:ALARM \\")
        print(f"    --data-file test_data.csv --verbose")
        print()
        print("Press Ctrl+C to stop the IOC")
        print("-"*60)
        
        # Set initial status to running
        self.status_pv.set(1)
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Keyboard interrupt received")
        finally:
            self.running = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] IOC shutting down...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Final counter value: {self.counter}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EPICS Test IOC - Heartbeat Generator")
    parser.add_argument('--device', '-d', default='TEST', 
                       help='Device name prefix for PVs (default: TEST)')
    parser.add_argument('--frequency', '-f', type=float, default=1.0,
                       help='Initial heartbeat frequency in Hz (default: 1.0)')
    
    args = parser.parse_args()
    
    # Validate frequency
    if not (0.1 <= args.frequency <= 10.0):
        print(f"Error: Frequency must be between 0.1 and 10.0 Hz, got {args.frequency}")
        sys.exit(1)
    
    # Create and run IOC
    ioc = HeartbeatIOC(device_name=args.device)
    ioc.frequency = args.frequency
    ioc.run()

if __name__ == '__main__':
    main()
