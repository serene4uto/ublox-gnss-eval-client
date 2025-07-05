# dashboard/main.py
import sys
from pathlib import Path
import argparse
import threading
from collections import deque
import socket
from logging import getLogger, StreamHandler, Formatter
import time
from typing import Optional
import json

import streamlit as st

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from dashboard.utils.logger import logger
from dashboard.utils.queue import ThreadSafeQueue
from dashboard.services.gnss_data_tcp_service import GNSSDataTCPService
from dashboard.views.sidebar import Sidebar



def arg_parser():
    parser = argparse.ArgumentParser(description="GNSS Dashboard Client")
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )
    
    return parser.parse_args()

def main():
    args = arg_parser()
    
    app_config = {
        "log_level": args.log_level.upper(),
    }
    
    logger.setLevel(app_config["log_level"])
    logger.info(f"Starting GNSS Dashboard Client with config: {app_config}")
    
    pages = [
        st.Page("pages/log_analysis.py", title="Log Analysis", icon="📊"),
        st.Page("pages/live_gnss.py", title="Live GNSS", icon="🛰️"),
        
    ]
    current_page = st.navigation(pages, position="sidebar", expanded=True)
    current_page.run()
    
    

if __name__ == "__main__":
    main()
