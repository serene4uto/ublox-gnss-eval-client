import streamlit as st
import threading
import time
import pandas as pd
import random

# Shared data dictionary for thread-safe communication
gnss_data = {"lat": 37.5665, "lon": 126.9780}

def fake_gnss_generator():
    while True:
        # Simulate GNSS data with a random walk
        gnss_data["lat"] += random.uniform(-0.0001, 0.0001)
        gnss_data["lon"] += random.uniform(-0.0001, 0.0001)
        time.sleep(1)  # Update every second

def main():
    # Start the background thread only once
    if "thread_started" not in st.session_state:
        threading.Thread(target=fake_gnss_generator, daemon=True).start()
        st.session_state["thread_started"] = True

    st.title("Real-Time Fake GNSS Map (with main function)")

    # Display current GNSS coordinates
    st.write(f"Current GNSS: {gnss_data}")

    # Show the point on a map
    data = pd.DataFrame({"lat": [gnss_data["lat"]], "lon": [gnss_data["lon"]]})
    st.map(data)

    # Auto-refresh the app every second for real-time updates
    # st.rerun()

if __name__ == "__main__":
    main()
