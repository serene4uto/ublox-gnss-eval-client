import streamlit as st
import pandas as pd
import threading
import time
import random
import pydeck as pdk
import numpy as np

# Helper function: convert numpy structured array row to dict
def numpy_row_to_dict(row):
    return {
        'lat': float(row['lat']),
        'lon': float(row['lon']),
        'accuracy': float(row['accuracy']),
        'timestamp': float(row['timestamp'])
    }

# Shared data store for GNSS data with fixed-size buffer
class GNSSDataStore:
    def __init__(self, max_size=5000):
        self.data = np.zeros(max_size, dtype=[
            ('lat', 'f8'),
            ('lon', 'f8'),
            ('accuracy', 'f8'),
            ('timestamp', 'f8')
        ])
        self.index = 0
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def add_data(self, point):
        with self.lock:
            self.data[self.index] = (
                point['lat'],
                point['lon'],
                point['accuracy'],
                point['timestamp']
            )
            self.index = (self.index + 1) % self.max_size
    
    def get_latest(self):
        with self.lock:
            if self.index > 0:
                return self.data[(self.index - 1) % self.max_size]
        return None
    
    def get_recent(self, count=10):
        with self.lock:
            if self.index == 0:
                return np.array([], dtype=self.data.dtype)
            start = max(0, self.index - count)
            return self.data[start:self.index]

# Initialize data store in session state
if 'store' not in st.session_state:
    st.session_state.store = GNSSDataStore(max_size=5000)

# Simulate GNSS data at 100Hz
def simulate_gnss_data(store, interval=0.01):
    def run():
        base_lat, base_lon = 36.1136, 128.336  # Gumi, South Korea
        while True:
            lat = base_lat + random.uniform(-0.001, 0.001)
            lon = base_lon + random.uniform(-0.001, 0.001)
            store.add_data({
                'lat': lat,
                'lon': lon,
                'accuracy': random.uniform(1.0, 5.0),
                'timestamp': time.time()
            })
            time.sleep(interval)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

# Start simulation thread only once
if 'thread_started' not in st.session_state:
    simulate_gnss_data(st.session_state.store, interval=0.01)
    st.session_state.thread_started = True

# Dashboard setup
st.set_page_config(page_title="100Hz GNSS Tracker", layout="wide")
st.title("Real-time GNSS Tracking @ 100Hz")
st.caption("Simulated GNSS data updating at 100Hz")

# Create layout placeholders
map_placeholder = st.empty()
metrics_placeholder = st.container()
data_placeholder = st.expander("Recent Data", expanded=False)
status_bar = st.empty()

# Performance monitoring
if 'frame_count' not in st.session_state:
    st.session_state.frame_count = 0
    st.session_state.last_update = time.time()

# Real-time update loop
while True:
    try:
        latest = st.session_state.store.get_latest()
        
        if latest is not None:
            # Performance counter
            st.session_state.frame_count += 1
            current_time = time.time()
            elapsed = current_time - st.session_state.last_update
            
            if elapsed >= 1.0:
                fps = st.session_state.frame_count / elapsed
                with status_bar:
                    st.caption(f"UI FPS: {fps:.1f} | Data Points: {len(st.session_state.store.get_recent(1)) if st.session_state.store.get_recent(1).size > 0 else 0}")
                st.session_state.frame_count = 0
                st.session_state.last_update = current_time
            
            # Update map
            latest_dict = numpy_row_to_dict(latest)
            df_map = pd.DataFrame([latest_dict])
            with map_placeholder:
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position="[lon, lat]",
                    get_radius=5,
                    radius_min_pixels=3,
                    radius_max_pixels=10,
                    get_fill_color=[255, 0, 0, 200],
                    pickable=True
                )
                view_state = pdk.ViewState(
                    latitude=latest_dict['lat'],
                    longitude=latest_dict['lon'],
                    zoom=19,
                    pitch=0,
                    bearing=0
                )
                # st.pydeck_chart(pdk.Deck(
                #     map_style='mapbox://styles/mapbox/light-v9',
                #     initial_view_state=view_state,
                #     layers=[layer],
                #     tooltip={"text": f"Lat: {latest_dict['lat']:.6f}°\nLon: {latest_dict['lon']:.6f}°"}
                # ))
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/satellite-v9',  # Satellite map
                    initial_view_state=view_state,
                    layers=[layer],
                    tooltip={"text": f"Lat: {latest_dict['lat']:.6f}°\nLon: {latest_dict['lon']:.6f}°"}
                ))
            
            # Update metrics
            with metrics_placeholder:
                col1, col2, col3 = st.columns(3)
                col1.metric("Latitude", f"{latest_dict['lat']:.6f}°")
                col2.metric("Longitude", f"{latest_dict['lon']:.6f}°")
                col3.metric("Accuracy", f"{latest_dict['accuracy']:.2f}m")
            
            # Update raw data table
            recent_data = st.session_state.store.get_recent(10)
            if recent_data.size > 0:
                recent_data_list = [numpy_row_to_dict(row) for row in recent_data]
                df_recent = pd.DataFrame(recent_data_list)
                with data_placeholder:
                    st.dataframe(df_recent, height=300, hide_index=True)
        
        time.sleep(0.01)  # 100Hz UI update
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        time.sleep(1)
