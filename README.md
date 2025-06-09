# Ublox GNSS Evaluation Client

This repository provides Python scripts to evaluate GNSS data streamed from the `ublox-gnss-streamer-py` repository (available at https://github.com/gumiInst/ublox-gnss-streamer-py).

The client receives GNSS data via a TCP connection. It then evaluates the following metrics by comparing the live data against a user-provided ground truth GNSS dataset:
*   Message rate
*   Horizontal Position Error (HPE)
*   Northing error
*   Easting error

Evaluation results are displayed on the console terminal and can be logged to files for further analysis and processing.


## How to Run

Run the GNSS evaluation client from your terminal using the following command structure:

```
python3 gnss_eval_tcp_client [OPTIONS]
```

The `[OPTIONS]` are command-line arguments that configure the client's behavior. CLI arguments will override settings from a YAML configuration file if one is used.

**Configuration File:**
*   `--yaml-config <FILE_PATH>`: Path to a YAML configuration file. Settings in this file can be overridden by command-line arguments.

**TCP Server Connection:**
*   `--tcp-host <IP_ADDRESS>`: IP address of the TCP server streaming GNSS data. (Default: `127.0.0.1`)
*   `--tcp-port <PORT_NUMBER>`: Port number of the TCP server. (Default: `50012`)

**Evaluation Parameters:**
*   `--eval-hz <RATE>`: The rate (in Hz) at which the processor thread reports evaluation results to the console and log file. (Default: `1.0`)
*   `--gt-lat <LATITUDE>`: Ground truth latitude in decimal degrees. (Default: `36.116588`)
*   `--gt-lon <LONGITUDE>`: Ground truth longitude in decimal degrees. (Default: `128.364695`)

**Logging Configuration:**
*   `--log-enable` / `--no-log-enable`: Enables or disables the logging of report data to a file. (Default: Logging is disabled)
*   `--log-file <FILE_PATH>`: Specifies the file path for logging report data. If `--log-enable` is used and this option is not provided (and not set in YAML), a default log file name will be generated in a `.gnss_log` directory (e.g., `.gnss_log/gnss_eval_127.0.0.1_50012_YYYYMMDD_HHMMSS.csv`).

**Example Command:**
```
python3 gnss_eval_tcp_client.py
--tcp-host 192.168.1.100
--tcp-port 50000
--gt-lat 35.123456
--gt-lon 129.654321
--eval-hz 2
--log-enable
--log-file ./evaluation_results/gnss_run1.csv
```

This command connects to a GNSS streamer at `192.168.1.100:50000`, uses the specified ground truth latitude and longitude, reports results at 2 Hz, enables logging, and saves the log to `./evaluation_results/gnss_run1.csv`.

To see a full list of available options, their default values, and descriptions, use the help flag:

```
python3 gnss_eval_tcp_client.py --help
```