import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
# Install dtaidistance: pip install dtaidistance
# from dtaidistance import dtw
from dtw import dtw

from haversine import haversine as hvs

st.set_page_config(page_title="GNSS Logs Analysis", page_icon="📊", layout="wide")
st.title("GNSS Logs Analysis")

# --- Haversine distance for GNSS traces ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2*R*np.arctan2(np.sqrt(a), np.sqrt(1-a))

def total_distance(df):
    if 'Latitude' in df.columns and 'Longitude' in df.columns and len(df) > 1:
        lats = df['Latitude'].values
        lons = df['Longitude'].values
        return float(np.sum(haversine(lats[:-1], lons[:-1], lats[1:], lons[1:])))
    return 0.0

# --- DTW Functions ---
def downsample_trace(trace, max_points=2000):
    """Downsample trace to reduce memory usage for DTW"""
    if len(trace) <= max_points:
        return trace
    
    # Use uniform sampling to preserve trace shape
    indices = np.linspace(0, len(trace) - 1, max_points, dtype=int)
    return [trace[i] for i in indices]



def calculate_dtw_distance(trace1, trace2, max_points=2000):
    """Calculate DTW distance and similarity score using dtaidistance"""
    try:
        # Downsample traces
        # trace1_sampled = downsample_trace(trace1, max_points)
        # trace2_sampled = downsample_trace(trace2, max_points)
        trace1_sampled = trace1
        trace2_sampled = trace2
        
        # Convert to numpy arrays and flatten for dtaidistance
        # dtaidistance expects 1D arrays, so we need to handle 2D GPS coordinates
        # trace1_array = np.array(trace1_sampled).flatten()
        # trace2_array = np.array(trace2_sampled).flatten()
        trace1_array = np.array(trace1_sampled, dtype=np.float64)
        trace2_array = np.array(trace2_sampled, dtype=np.float64)
        
        # Use optimized DTW from dtaidistance
        # dtw_distance = dtw.distance_fast(trace1_array, trace2_array)
        
        def gnss_distance(x, y):
            """Calculate distance between two (lat, lon) points in meters."""
            return hvs((x[0], x[1]), (y[0], y[1]), unit='m')
        
        alignment = dtw(
            trace1_array,
            trace2_array,
            dist_method=gnss_distance,  # Use the correct parameter
            keep_internals=True
        )
        dtw_distance = alignment.normalizedDistance
        
        # Calculate similarity score (0-1 scale, higher = more similar)
        similarity_score = 1 / (1 + dtw_distance)
        
        return dtw_distance, similarity_score
        
    except MemoryError:
        pass
        # # If still out of memory, try with even fewer points
        # trace1_small = downsample_trace(trace1, 500)
        # trace2_small = downsample_trace(trace2, 500)
        
        # trace1_array = np.array(trace1_small).flatten()
        # trace2_array = np.array(trace2_small).flatten()
        
        # distance = dtw.distance_fast(trace1_array, trace2_array)
        # similarity_score = 1 / (1 + distance)
        
        # return distance, similarity_score

def get_lat_lon_pairs(df):
    """Extract lat/lon pairs from dataframe"""
    if df is not None and 'Latitude' in df.columns and 'Longitude' in df.columns:
        return df[['Latitude', 'Longitude']].values.tolist()
    return []

# --- Session State Initialization ---
if "gnss_file_tabs" not in st.session_state:
    st.session_state.gnss_file_tabs = ["File 1"]
if "logs_data" not in st.session_state:
    st.session_state.logs_data = {}  # {tab_name: DataFrame}
if "logs_analysis" not in st.session_state:
    st.session_state.logs_analysis = {}  # {tab_name: analysis_result}

# --- Helper function to delete a tab ---
def delete_log_tab(tab_name):
    if tab_name in st.session_state.gnss_file_tabs:
        st.session_state.gnss_file_tabs.remove(tab_name)
    st.session_state.logs_data.pop(tab_name, None)
    st.session_state.logs_analysis.pop(tab_name, None)

# --- Helper function to reorder tabs and associated data ---
def reorder_tabs_and_data():
    # Save current data
    old_tabs = st.session_state.gnss_file_tabs.copy()
    new_tabs = [f"File {i+1}" for i in range(len(old_tabs))]
    new_logs_data = {}
    new_logs_analysis = {}
    for new_name, old_name in zip(new_tabs, old_tabs):
        if old_name in st.session_state.logs_data:
            new_logs_data[new_name] = st.session_state.logs_data[old_name]
        if old_name in st.session_state.logs_analysis:
            new_logs_analysis[new_name] = st.session_state.logs_analysis[old_name]
    # Update session state
    st.session_state.gnss_file_tabs = new_tabs
    st.session_state.logs_data = new_logs_data
    st.session_state.logs_analysis = new_logs_analysis

# --- Add New Tab Button ---
with st.container():
    st.subheader("Single Log Analysis (Multiple Tabs)")
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("➕ Add GNSS File Tab"):
            new_tab_name = f"File {len(st.session_state.gnss_file_tabs) + 1}"
            st.session_state.gnss_file_tabs.append(new_tab_name)

# --- Tabs for Logs ---
tabs = st.tabs(st.session_state.gnss_file_tabs)
for i, tab in enumerate(tabs):
    with tab:
        tab_name = st.session_state.gnss_file_tabs[i]
        st.markdown(f"#### {tab_name}")

        # --- Delete Tab Button ---
        delete_col, rest_col = st.columns([1, 8])
        with delete_col:
            # Only allow delete if more than one tab remains
            if len(st.session_state.gnss_file_tabs) > 1:
                if st.button("🗑️", key=f"delete_{tab_name}"):
                    delete_log_tab(tab_name)
                    reorder_tabs_and_data()
                    st.rerun()  # Refresh to update tabs
            else:
                st.markdown(" ")

        # --- File Uploader ---
        uploaded_file = st.file_uploader(
            f"Upload GNSS log file for {tab_name} (CSV)",
            type=["csv"],
            key=f"uploader_{tab_name}"
        )
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            # Exclude unwanted columns
            exclude_cols = ['HPE(m)', 'NorthingError(m)', 'EastingError(m)']
            df = df.drop(columns=[col for col in exclude_cols if col in df.columns])
            st.session_state.logs_data[tab_name] = df
        else:
            df = st.session_state.logs_data.get(tab_name)

        if df is not None:
            st.write(f"**Preview of {tab_name}:**")
            with st.expander("Show Data"):
                st.dataframe(df)
            # FixType filter
            fix_types = sorted(df["FixType"].dropna().unique()) if "FixType" in df.columns else []
            selected_fix_types = st.multiselect(
                f"Select FixType(s) for {tab_name}",
                options=fix_types,
                default=fix_types,
                key=f"fix_type_{tab_name}"
            ) if fix_types else []
            filtered_df = df[df["FixType"].isin(selected_fix_types)] if selected_fix_types else df

            if st.button(f"Analyze {tab_name}", key=f"analyze_{tab_name}"):
                result = {}
            
                # Parse TimestampKST (ISO 8601 with timezone)
                try:
                    filtered_df = filtered_df.copy()  # Avoid SettingWithCopyWarning
                    filtered_df['TimestampKST'] = pd.to_datetime(filtered_df['TimestampKST'], format='ISO8601')
                    trace_duration = filtered_df['TimestampKST'].iloc[-1] - filtered_df['TimestampKST'].iloc[0]
                    duration_seconds = trace_duration.total_seconds()
                    result["Trace Duration"] = str(trace_duration)
                    result["Sampling Rate (Hz)"] = round(len(filtered_df) / duration_seconds, 3) if duration_seconds > 0 else "N/A"
                except Exception as e:
                    print(f"Error parsing TimestampKST: {e}")
                    result["Trace Duration"] = "N/A"
                    result["Sampling Rate (Hz)"] = "N/A"
            
                # Latitude/Longitude Range and Total Distance
                if "Latitude" in filtered_df.columns and "Longitude" in filtered_df.columns:
                    result["Latitude Range"] = [float(filtered_df['Latitude'].min()), float(filtered_df['Latitude'].max())]
                    result["Longitude Range"] = [float(filtered_df['Longitude'].min()), float(filtered_df['Longitude'].max())]
                    dist = total_distance(filtered_df)
                    result["Total Distance (meters)"] = round(dist, 2) if dist is not None else "N/A"
                else:
                    result["Latitude Range"] = "N/A"
                    result["Longitude Range"] = "N/A"
                    result["Total Distance (meters)"] = "N/A"
            
                # FixType Distribution
                if "FixType" in filtered_df.columns:
                    fix_counts = filtered_df["FixType"].value_counts().to_dict()
                    result["FixType Distribution"] = fix_counts
            
                st.session_state.logs_analysis[tab_name] = result
                st.success(f"Analysis of {tab_name} completed!")
            
            # --- Display analysis results in a user-friendly way ---
            if tab_name in st.session_state.logs_analysis:
                st.info(f"Analysis Result for {tab_name}:")
                res = st.session_state.logs_analysis[tab_name]
            
                # Show main metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Trace Duration", res.get("Trace Duration", "N/A"))
                    st.metric("Sampling Rate (Hz)", res.get("Sampling Rate (Hz)", "N/A"))
                    st.metric("Total Distance (meters)", res.get("Total Distance (meters)", "N/A"))
                with col2:
                    lat_range = res.get("Latitude Range", ["N/A", "N/A"])
                    lon_range = res.get("Longitude Range", ["N/A", "N/A"])
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        st.metric("Latitude Min", lat_range[0] if isinstance(lat_range, list) else "N/A")
                        st.metric("Latitude Max", lat_range[1] if isinstance(lat_range, list) else "N/A")
                    with sub_col2:
                        st.metric("Longitude Min", lon_range[0] if isinstance(lon_range, list) else "N/A")
                        st.metric("Longitude Max", lon_range[1] if isinstance(lon_range, list) else "N/A")
            
                # Show FixType distribution as a table
                if "FixType Distribution" in res:
                    st.subheader("FixType Distribution")
                    fix_df = pd.DataFrame(
                        list(res["FixType Distribution"].items()), columns=["FixType", "Count"]
                    )
                    st.table(fix_df)
                    
            # --- Plot Map Button ---
            if st.button(f"Plot Map for {tab_name}", key=f"plot_map_{tab_name}"):
                if "Latitude" in filtered_df.columns and "Longitude" in filtered_df.columns:
                    # Prepare DataFrame for Pydeck
                    map_df = filtered_df[["Latitude", "Longitude"]].copy()
                    map_df.rename(columns={"Latitude": "lat", "Longitude": "lon"}, inplace=True)

                    # Calculate center and zoom
                    lat = map_df["lat"].mean()
                    lon = map_df["lon"].mean()
                    zoom = 14  # You can adjust zoom as needed

                    # Save to session_state for compatibility with your code
                    st.session_state.df = map_df

                    # Pydeck layers
                    layers = [
                        pdk.Layer(
                            "PathLayer",
                            data=[{"path": map_df[["lon", "lat"]].values.tolist()}],
                            get_path='path',
                            get_color=[255, 0, 0, 255],  # Bright red, fully opaque
                            get_width=0.01,
                            pickable=True,
                            width_scale=20,
                            width_min_pixels=5,
                        ),
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=pd.DataFrame([map_df.iloc[-1]]),  # Last point
                            get_position='[lon, lat]',
                            get_color=[200, 30, 0, 160],
                            get_radius=50,  # Make it visible
                        ),
                    ]

                    st.pydeck_chart(
                        pdk.Deck(
                            map_style='mapbox://styles/mapbox/satellite-v9',
                            initial_view_state=pdk.ViewState(
                                latitude=lat,
                                longitude=lon,
                                zoom=zoom,
                            ),
                            layers=layers,
                        )
                    )
                else:
                    st.warning("Latitude/Longitude columns are required to plot the map.")
        else:
            st.info("Please upload a log file.")

# --- Comparison Section ---
st.divider()
st.header("GNSS File Comparison")

# Only show comparison if at least 2 logs are uploaded
available_logs = [name for name, df in st.session_state.logs_data.items() if df is not None]
if len(available_logs) >= 2:
    colA, colB = st.columns(2)
    with colA:
        logA = st.selectbox("Select File A", options=available_logs, key="compare_log_a")
    with colB:
        logB = st.selectbox("Select File B", options=[l for l in available_logs if l != logA], key="compare_log_b")

    dfA = st.session_state.logs_data.get(logA)
    dfB = st.session_state.logs_data.get(logB)

    # FixType filters for each log
    fix_types_A = sorted(dfA["FixType"].dropna().unique()) if "FixType" in dfA.columns else []
    fix_types_B = sorted(dfB["FixType"].dropna().unique()) if "FixType" in dfB.columns else []

    selected_fix_types_A = st.multiselect(
        f"Select FixType(s) for {logA}",
        options=fix_types_A,
        default=fix_types_A,
        key="compare_fix_type_A"
    ) if fix_types_A else []
    selected_fix_types_B = st.multiselect(
        f"Select FixType(s) for {logB}",
        options=fix_types_B,
        default=fix_types_B,
        key="compare_fix_type_B"
    ) if fix_types_B else []

    filtered_dfA = dfA[dfA["FixType"].isin(selected_fix_types_A)] if selected_fix_types_A else dfA
    filtered_dfB = dfB[dfB["FixType"].isin(selected_fix_types_B)] if selected_fix_types_B else dfB

    if st.button("Compare Selected Logs"):
        
        # plot 2 traces on map
        if "Latitude" in filtered_dfA.columns and "Longitude" in filtered_dfA.columns and \
           "Latitude" in filtered_dfB.columns and "Longitude" in filtered_dfB.columns:
            map_dfA = filtered_dfA[["Latitude", "Longitude"]].copy()
            map_dfA.rename(columns={"Latitude": "lat", "Longitude": "lon"}, inplace=True)
            map_dfB = filtered_dfB[["Latitude", "Longitude"]].copy()
            map_dfB.rename(columns={"Latitude": "lat", "Longitude": "lon"}, inplace=True)   
            # Calculate center and zoom for both traces
            latA = map_dfA["lat"].mean()
            lonA = map_dfA["lon"].mean()
            latB = map_dfB["lat"].mean()
            lonB = map_dfB["lon"].mean()
            zoom = 14  # You can adjust zoom as needed
            
            layers = [
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": map_dfA[["lon", "lat"]].values.tolist()}],
                    get_path='path',
                    get_color=[255, 0, 0, 255],  # Bright red, fully opaque
                    get_width=0.01,
                    pickable=True,
                    width_scale=20,
                    width_min_pixels=5,
                ),
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": map_dfB[["lon", "lat"]].values.tolist()}],
                    get_path='path',
                    get_color=[0, 0, 255, 255],  # Bright blue, fully opaque
                    get_width=0.01,
                    pickable=True,
                    width_scale=20,
                    width_min_pixels=5,
                ),
            ]
            
            st.pydeck_chart(
                pdk.Deck(
                    map_style='mapbox://styles/mapbox/satellite-v9',
                    initial_view_state=pdk.ViewState(
                        latitude=(latA + latB) / 2,
                        longitude=(lonA + lonB) / 2,
                        zoom=zoom,
                    ),
                    layers=layers,
                )
            )
        
        distA = total_distance(filtered_dfA)
        distB = total_distance(filtered_dfB)
        
        # Calculate DTW similarity
        traceA = get_lat_lon_pairs(filtered_dfA)
        traceB = get_lat_lon_pairs(filtered_dfB)
        dtw_distance = None
        similarity_score = None
        if traceA and traceB:
            try:
                dtw_distance, similarity_score = calculate_dtw_distance(traceA, traceB)
            except Exception as e:
                st.warning(f"DTW calculation failed: {str(e)}")
        
        comparison = {
            f"{logA} Total Distance (meters)": round(distA, 2) if distA is not None else "N/A",
            f"{logB} Total Distance (meters)": round(distB, 2) if distB is not None else "N/A",
            "Distance Difference (meters)": round(abs(distA - distB), 2) if distA is not None and distB is not None else "N/A",
            f"{logA} Points After Filter": len(filtered_dfA),
            f"{logB} Points After Filter": len(filtered_dfB),
            "DTW Distance": round(dtw_distance, 4) if dtw_distance is not None else "N/A",
            "Similarity Score": f"{round(similarity_score * 100, 1)}%" if similarity_score is not None else "N/A"
        }
        st.session_state["comparison_result"] = comparison
        st.success("Comparison completed!")

    if st.session_state.get("comparison_result") is not None:
        st.info("Comparison Result:")
        result = st.session_state["comparison_result"]
        
        # Create columns for better layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                f"{logA} Total Distance (m)",
                result.get(f"{logA} Total Distance (meters)", "N/A")
            )
            st.metric(
                f"{logA} Points",
                result.get(f"{logA} Points After Filter", "N/A")
            )
        
        with col2:
            st.metric(
                f"{logB} Total Distance (m)",
                result.get(f"{logB} Total Distance (meters)", "N/A")
            )
            st.metric(
                f"{logB} Points",
                result.get(f"{logB} Points After Filter", "N/A")
            )
        
        with col3:
            st.metric(
                "Distance Difference (m)",
                result.get("Distance Difference (meters)", "N/A")
            )
            st.metric(
                "DTW Similarity Distance",
                result.get("DTW Distance", "N/A"),
                help="Lower values indicate more similar trace patterns"
            )
            st.metric(
                "Similarity Score",
                result.get("Similarity Score", "N/A"),
                help="Higher percentage indicates more similar traces"
            )
else:
    st.warning("Upload at least two logs to enable comparison.")
