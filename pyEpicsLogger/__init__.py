"""
pyEpicsLogger - Multi-Channel EPICS Process Variable Logger

A command-line tool to monitor multiple EPICS Process Variable channels 
and log all value changes with timestamps to CSV files.

Author: Jacob Taylor (jacobataylor7@gmail.com)
GitHub: https://github.com/jacotay7/pyEpicsLogger
"""

__version__ = "1.0.0"
__author__ = "Jacob Taylor"
__email__ = "jacobataylor7@gmail.com"
__license__ = "MIT"

from .epicsLogger import EPICSLogger

__all__ = ["EPICSLogger"]
