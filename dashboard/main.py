# dashboard/main.py
import argparse
import threading
from collections import deque
import socket
from logging import getLogger, StreamHandler, Formatter
import time
from typing import Optional
import json

from dashboard.utils.logger import logger
from dashboard.utils.queue import ThreadSafeQueue


def arg_parser():
    parser = argparse.ArgumentParser(description="GNSS Dashboard Client")
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host address of the GNSS data server (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port number of the GNSS data server (default: 5000)",
    )
    
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
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.upper(),
    }
    
    logger.setLevel(app_config["log_level"])
    logger.info(f"Starting GNSS Dashboard Client with config: {app_config}")
    
    stop_event = threading.Event()
    data_queue = ThreadSafeQueue(max_size=50) 

if __name__ == "__main__":
    main()
