import serial
import time
import collections
from threading import Thread, Event, Lock

from pyubx2 import (
    NMEA_PROTOCOL,
    RTCM3_PROTOCOL,
    UBX_PROTOCOL,
    UBXMessage,
    UBXMessageError,
    UBXParseError,
    UBXReader,
)


# For this script to be self-contained, here is a simple implementation 
# of a thread-safe deque.
class ThreadSafeDeque:
    """
    A deque implementation that is safe to use across multiple threads.
    """
    def __init__(self, *args, **kwargs):
        self._deque = collections.deque(*args, **kwargs)
        self._lock = Lock()

    def append(self, item):
        with self._lock:
            self._deque.append(item)

    def popleft(self):
        with self._lock:
            return self._deque.popleft()

    def is_empty(self):
        with self._lock:
            return len(self._deque) == 0
            
    def __len__(self):
        with self._lock:
            return len(self._deque)


class GNSSService:
    """
    A service that connects to a GNSS device via a serial port and reads
    NMEA messages in a background thread.
    """
    def __init__(
        self, 
        port: str, 
        baudrate: int, 
        timeout: float,
        **kwargs
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        
        self._ubr:UBXReader = None
        self._stop_event = Event()
        self._thread: Thread = None
        self._data_queue = ThreadSafeDeque(maxlen=100)
    
    def _device_connect(self):
        """
        Connect to the GNSS device via serial port.
        Returns True on success, False on failure.
        """
        try:
            print(f"Attempting to connect to {self.port}...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self._ubr = UBXReader(self.serial_connection, protfilter=NMEA_PROTOCOL)
            print("Successfully connected to GNSS device.")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to GNSS device: {e}")
            self.serial_connection = None
            return False
    
    def _device_disconnect(self):
        """
        Disconnect from the GNSS device.
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("GNSS device disconnected.")
        self.serial_connection = None
    
    def _loop(self):
        """
        Main loop to read data from the GNSS device.
        This method runs in a background thread.
        """
        while not self._stop_event.is_set():
            # --- Robust Reconnection Logic ---
            if self.serial_connection is None or not self.serial_connection.is_open:
                if not self._device_connect():
                    # Wait for 5 seconds before retrying connection
                    self._stop_event.wait(5)
                    continue
            
            # --- Data Reading Logic ---
            try:
                raw, parsed = self._ubr.read()
                print(f"Raw data: {raw}, Parsed data: {parsed}")
                if parsed and hasattr(parsed, "identity"):
                    if parsed.identity == "GNGGA":
                        if isinstance(raw, bytes):
                            self._data_queue.append(
                                raw.decode('utf-8', errors='replace'))
            except Exception as e:
                print(f"Error reading data: {e}")
    
    def start(self):
        """
        Start the GNSS service in a background thread.
        """
        if self.is_running():
            print("GNSS service is already running.")
            return

        print("Starting GNSS service...")
        self._stop_event.clear() # Clear event in case of a restart
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("GNSS service started.")
    
    def stop(self):
        """
        Stop the GNSS service gracefully.
        """
        if not self.is_running():
            print("GNSS service is not running.")
            return

        print("Stopping GNSS service...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0) # Wait for thread to finish
        
        self._device_disconnect()
        print("GNSS service stopped.")
    
    def is_running(self) -> bool:
        """Check if the service thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def get_data(self):
        """
        Retrieve one NMEA message from the queue.
        Returns the message string or None if the queue is empty.
        """
        if not self._data_queue.is_empty():
            return self._data_queue.popleft()
        return None


# --- Test Block ---
if __name__ == "__main__":
    # --- Configuration ---
    # On Linux, this might be /dev/ttyUSB0 or /dev/ttyACM0
    # On Windows, this will be something like COM3
    SERIAL_PORT = "/dev/ttyUSB0" 
    BAUD_RATE = 115200
    
    gnss_service = GNSSService(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        timeout=1.0  # Read timeout in seconds
    )
    
    gnss_service.start()
    
    # Keep the main thread running to process data and handle shutdown
    try:
        while gnss_service.is_running():
            # Get data from the service
            nmea_message = gnss_service.get_data()
            if nmea_message:
                print(f"Main Thread | Received: {nmea_message}")
            
            # Sleep to prevent high CPU usage
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down.")
    finally:
        # --- Graceful Shutdown ---
        gnss_service.stop()
        
    print("Main program finished.")
