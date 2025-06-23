import threading
import socket
from typing import Optional

from dashboard.utils.queue import ThreadSafeQueue
from dashboard.utils.logger import logger

class GNSSDataTCPService:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        buffer_size: int = 4096,
        max_buffer: int = 10 * 1024 * 1024  # 10MB max buffer
    ):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.max_buffer = max_buffer
        
        # Internal state management
        self._stop_event = threading.Event()
        self._data_queue = ThreadSafeQueue(max_size=100)  # Thread-safe queue for data
        self._thread: Optional[threading.Thread] = None
        self.sock: Optional[socket.socket] = None

    def start(self) -> bool:
        """Start the service and return True if started successfully"""
        if self.is_running:
            logger.warning("Service is already running")
            return False
            
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f"GNSSService-{self.host}:{self.port}"
        )
        self._thread.start()
        logger.info(f"Started GNSS TCP service on {self.host}:{self.port}")
        return True

    @property
    def is_running(self) -> bool:
        """Check if service is running"""
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        """Stop the service gracefully"""
        if not self.is_running:
            logger.warning("Service is not running")
            return
            
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        
        if self._thread.is_alive():
            logger.error("Service thread failed to terminate")
        else:
            logger.info("GNSS TCP service stopped")
            self._thread = None

    def get_data(self, block: bool = True, timeout: float = None) -> Optional[str]:
        """Get data from the queue (thread-safe)"""
        try:
            return self._data_queue.get(block=block, timeout=timeout)
        except Exception as e:
            logger.error(f"Data retrieval error: {e}")
            return None

    def _run(self):
        data_buffer = b""
        
        try:
            self.sock = socket.create_connection(
                (self.host, self.port),
                timeout=5.0
            )
            self.sock.settimeout(0.1)
            logger.info(f"Connected to GNSS server at {self.host}:{self.port}")
            
            while not self._stop_event.is_set():
                try:
                    chunk = self.sock.recv(self.buffer_size)
                    if not chunk:
                        logger.info("Server closed connection")
                        break
                        
                    data_buffer += chunk
                    
                    if len(data_buffer) > self.max_buffer:
                        logger.error("Buffer overflow detected")
                        break
                        
                    data_buffer = self._process_buffer(data_buffer)
                    
                except socket.timeout:
                    continue
                except OSError as e:
                    if not self._stop_event.is_set():
                        logger.error(f"Socket error: {e}")
                    break
                    
        except (socket.error, ConnectionError) as e:
            logger.error(f"Connection failed: {e}")
        finally:
            self._cleanup()

    def _process_buffer(self, data_buffer: bytes) -> bytes:
        """Process complete messages from buffer"""
        while b'\n' in data_buffer and not self._stop_event.is_set():
            message_bytes, data_buffer = data_buffer.split(b'\n', 1)
            try:
                msg_str = message_bytes.decode('utf-8', errors='replace').strip()
                if msg_str:
                    self._data_queue.put(msg_str)
            except UnicodeDecodeError as ude:
                logger.warning(f"Decode error: {ude}. Partial: {message_bytes[:50]}")
            except Exception as e:
                logger.error(f"Message processing error: {e}")
        return data_buffer

    def _cleanup(self):
        """Safe resource cleanup"""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self.sock.close()
                self.sock = None
        self._stop_event.set()