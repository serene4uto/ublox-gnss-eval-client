import argparse
import threading
from collections import deque
import socket
from logging import getLogger, StreamHandler, Formatter
import time
from typing import Optional
import json

import requests
import streamlit as st
import pydeck as pdk
import pandas as pd

# setup logging
logger = getLogger("GNSSDashboardClient")
handler = StreamHandler()
handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel("DEBUG")


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


class ThreadSafeQueue:
    def __init__(self, max_size=1000):
        self.queue = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def put(self, item):
        with self.lock:
            self.queue.append(item)

    def get(self):
        with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None

    def is_empty(self):
        with self.lock:
            return len(self.queue) == 0

    def size(self):
        with self.lock:
            return len(self.queue)


class GNSSDataTCPClientWorker:
    def __init__(
        self,
        stop_event: threading.Event,
        data_queue: ThreadSafeQueue,
        host: str = "localhost",
        port: int = 5000,
        buffer_size: int = 4096,
        max_buffer: int = 10 * 1024 * 1024  # 10MB max buffer
    ):
        self.stop_event = stop_event
        self.data_queue = data_queue
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.max_buffer = max_buffer
        self._thread: Optional[threading.Thread] = None
        self.sock: Optional[socket.socket] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("Worker thread is already running.")
            return
            
        self._thread = threading.Thread(
            target=self.run,
            daemon=True,
            name=f"GNSSClient-{self.host}:{self.port}"
        )
        self._thread.start()
        logger.info(f"Started GNSSDataTCPClientWorker on {self.host}:{self.port}")

    def run(self):
        data_buffer = b""
        
        try:
            self.sock = socket.create_connection(
                (self.host, self.port),
                timeout=5.0  # Connection timeout
            )
            self.sock.settimeout(0.1)  # Recv timeout
            logger.info(f"Connected to GNSS server at {self.host}:{self.port}")
            
            while not self.stop_event.is_set():
                try:
                    chunk = self.sock.recv(self.buffer_size)
                    if not chunk:
                        logger.info("Server closed connection")
                        break
                        
                    data_buffer += chunk
                    
                    # Prevent buffer overflow
                    if len(data_buffer) > self.max_buffer:
                        logger.error("Buffer overflow detected")
                        break
                        
                    self._process_buffer(data_buffer)
                    
                except socket.timeout:
                    continue
                except OSError as e:
                    if not self.stop_event.is_set():
                        logger.error(f"Socket error: {e}")
                    break
                    
        except (socket.error, ConnectionError) as e:
            logger.error(f"Connection failed: {e}")
        finally:
            self._cleanup()
            logger.info("Connection closed")

    def _process_buffer(self, data_buffer: bytes) -> bytes:
        """Process complete messages from buffer"""
        while b'\n' in data_buffer and not self.stop_event.is_set():
            message_bytes, data_buffer = data_buffer.split(b'\n', 1)
            try:
                msg_str = message_bytes.decode('utf-8', errors='replace').strip()
                if msg_str:
                    # Use queue's own thread-safety mechanism
                    self.data_queue.put(msg_str)
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

    def stop(self):
        if self._thread and self._thread.is_alive():
            self.stop_event.set()
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                logger.error("Worker thread failed to terminate")
            else:
                logger.info("GNSSDataTCPClientWorker stopped")
        else:
            logger.warning("No active worker thread to stop")
       


class StDashboardUI:
    """
    Streamlit Dashboard UI for GNSS Data Visualization.
    """
    
    st.set_page_config(
        page_title="GNSS Dashboard",
        page_icon="🌍",
        layout="wide",
    )
    
    def __init__(
        self,
        stop_event: threading.Event,
        gnss_data_queue: ThreadSafeQueue,
        update_interval: float = 1.0,
    ):
        self.stop_event = stop_event
        self.gnss_data_queue = gnss_data_queue
        self.update_interval = update_interval
        self._init_session_state()
        

    def start(self):
        """
        Start the Streamlit dashboard UI.
        """
        self._init_ui()
        self._render_ui()

    def _init_session_state(self):
        """Initialize session state if needed."""
        if 'gnss_data_queue' not in st.session_state:
            st.session_state.gnss_data_queue = self.gnss_data_queue
        if 'stop_event' not in st.session_state:
            st.session_state.stop_event = self.stop_event
            
        if 'df' not in st.session_state:
            st.session_state.df = pd.DataFrame({
                'lat': [],
                'lon': [],
            })
            
    def _init_ui(self):
        """Initialize the Streamlit UI components."""
        
        st.title("GNSS Dashboard")
        st.sidebar.title("Control Panel")
        
        self.sidebar_display = st.sidebar.empty()
        self.map_column, self.metrics_column = st.columns([2, 1])
        self.map_display = self.map_column.empty()
        self.metrics_display = self.metrics_column.empty()

    def _render_ui(self):
        """Render the main Streamlit UI components."""
        
        while True:
            # Control update frequency
            time.sleep(self.update_interval)
            
            # Simulate new data (replace with your real data source)
            if st.session_state.gnss_data_queue.is_empty():
                continue
            
            json_data = st.session_state.gnss_data_queue.get()
            
            if not json_data:
                continue
            
            try:
                data = json.loads(json_data)
                new_lat = data.get('lat')  
                new_lon = data.get('lon')
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                continue
            
            
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame({'lat': [new_lat], 'lon': [new_lon]})],
                ignore_index=True
            )
            
            # Update the map and metrics
            self._update_map(new_lat, new_lon)
            self._update_metrics(new_lat, new_lon)

    def _update_map(self, lat, lon, zoom=11):
        """Update the map with new GNSS data."""
        with self.map_display.container():
            
            if st.session_state.df.empty:
                st.write("No GNSS data available yet.")
                return
            
            # prepare layers
            layers = []
            
            layers = [
                pdk.Layer(
                    'ScatterplotLayer',
                    data=pd.DataFrame([st.session_state.df.iloc[-1]]),
                    get_position='[lon, lat]',
                    get_color=[200, 30, 0, 160],
                    get_radius=1,
                ),
                pdk.Layer(
                    'PathLayer',
                    data=[{"path": st.session_state.df[['lon', 'lat']].values.tolist()}],
                    get_path='path',
                    get_color=[255, 0, 0, 255],  # Bright red, fully opaque
                    get_width=0.01,  # Increased width
                    pickable=True,
                    width_scale=20,  # Scale the width
                    width_min_pixels=5,  # Ensure minimum width
                ),
            ]
            
            st.pydeck_chart(
                pdk.Deck(
                    map_style='mapbox://styles/mapbox/satellite-v9',
                    initial_view_state=pdk.ViewState(
                        latitude=lat,
                        longitude=lon,
                        zoom=zoom
                    ),
                    layers=layers,
                )
            )
        

    def _update_metrics(self, lat, lon):
        """Update the metrics with new GNSS data."""
        with self.metrics_display.container():
            st.metric("Latitude", value=f"{lat:.6f}°")
            st.metric("Longitude", value=f"{lon:.6f}°")
            

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
    
    gnss_tcp_client_worker = GNSSDataTCPClientWorker(
        stop_event=stop_event,
        data_queue=data_queue,
        host=app_config["host"],
        port=app_config["port"]
    )
    gnss_tcp_client_worker.start()
    
    # # keep main thread for streamlit dashboard
    
    st_dashboard_ui = StDashboardUI(
        stop_event=stop_event,
        gnss_data_queue=data_queue,
        update_interval=0.01,  # Update interval in seconds
    )
    st_dashboard_ui.start()
    
    # while True:
    #     time.sleep(1)
    
    

if __name__ == "__main__":
    main()