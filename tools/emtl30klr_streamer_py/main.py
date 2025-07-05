import sys
import argparse
import yaml
import logging
from threading import Thread, Event

import serial

from emtl30klr_streamer_py.utils.logger import logger, ColoredFormatter, ColoredLogger


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="ublox_gnss_streamer"
    )
    
    # YAML config file
    parser.add_argument(
        "-y", "--yaml-config", type=str,
        help="Path to YAML configuration file",
        default=argparse.SUPPRESS
    )
    
    # Ublox GNSS parameters
    parser.add_argument(
        "-p", "--serial-port", type=str,
        help="Serial port to connect to the GNSS device",
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-b", "--serial-baudrate", type=int,
        help="Baudrate for the serial connection",
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-t", "--serial-timeout", type=float,
        help="Timeout in secs for the serial connection",
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-i", "--serial-interface", type=str,
        help="Serial interface used on the module (e.g., UART1, USB, etc.)",
        default=argparse.SUPPRESS
    )

    # TCP publisher parameters
    parser.add_argument(
        "-a", "--tcp-host", type=str,
        help="TCP host to publish data to",
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-q", "--tcp-port", type=int,
        help="TCP port to publish data to",
        default=argparse.SUPPRESS
    )

    # others
    parser.add_argument(
        "-l", "--logger-level",
        choices=["debug", "info", "warning", "fatal", "error"],
        help="Set the logger level",
        default=argparse.SUPPRESS
    )

    return parser.parse_args(argv)



def main(argv=None):
    args = parse_args(argv)

    # Prepare a dictionary of final config values
    config_dict = {}

    # Load YAML config if provided
    if hasattr(args, 'yaml_config'):
        try:
            with open(args.yaml_config, 'r') as file:
                yaml_config = yaml.safe_load(file)
                if yaml_config:
                    config_dict.update(yaml_config)
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML config file {args.yaml_config}: {e}") from e

    # Override YAML config with CLI arguments (if set by user, not default)
    for key, value in vars(args).items():
        config_dict[key] = value
            
    # Set up logging
    logger.setLevel(getattr(logging, config_dict.get('logger_level', 'info').upper()))
    if not logger.hasHandlers():
        # This block ensures that the logger has a handler after class change
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, config_dict.get('logger_level', 'info').upper()))
        formatter = ColoredFormatter(ColoredLogger.FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    logger.info("Starting ublox_gnss_streamer")
    
    # Log the final configuration
    for key, value in config_dict.items():
        logger.info(f"Config {key}: {value}")
        
    stop_event = Event()
    



if __name__ == "__main__":
    main()