#!/usr/bin/env python3
"""
Main entry point for the Telegram Analyzer application.

This script provides a simple way to run the application from the command line.
"""

import sys
from telegram_analyzer.cli import main

if __name__ == "__main__":
    sys.exit(main())