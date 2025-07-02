import streamlit as st
import pydeck as pdk
import pandas as pd

from dashboard.utils.logger import logger

st.set_page_config(
    page_title="Live GNSS",
    page_icon="🛰️",
    layout="wide"
)

st.title("Live GNSS")

@st.fragment(run_every=0.01)
def map_update():
    # Map placeholder
    with st.empty().container():

        layers = [
            # pdk.Layer(
            #     'ScatterplotLayer',
            #     data=pd.DataFrame([st.session_state.df.iloc[-1]]),
            #     get_position='[lon, lat]',
            #     get_color=[200, 30, 0, 160],
            #     get_radius=1,
            # ),
            # pdk.Layer(
            #     'PathLayer',
            #     data=[{"path": st.session_state.df[['lon', 'lat']].values.tolist()}],
            #     get_path='path',
            #     get_color=[255, 0, 0, 255],  # Bright red, fully opaque
            #     get_width=0.01,  # Increased width
            #     pickable=True,
            #     width_scale=20,  # Scale the width
            #     width_min_pixels=5,  # Ensure minimum width
            # ),
        ]

        st.pydeck_chart(
            pdk.Deck(
                map_style='mapbox://styles/mapbox/satellite-v9',
                # initial_view_state=pdk.ViewState(
                #     latitude=lat,
                #     longitude=lon,
                #     zoom=zoom
                # ),
                layers=layers,
            )
        )
        
map_update()

# GNSS Data Receivers
with st.empty().container():
    
    def render_gnss_data_receiver(id: int):
        # Initialize connection state
        if f"gnss_stream_{id}_connected" not in st.session_state:
            st.session_state[f"gnss_stream_{id}_connected"] = False
        
        st.subheader(f"GNSS Stream {id}")
        cols = st.columns(3)
        with cols[0]:
            st.text_input(
                "Host",
                value="localhost",
                key=f"gnss_stream_{id}_host",
                disabled=st.session_state[f"gnss_stream_{id}_connected"]
            )
        with cols[1]:
            st.text_input(
                "Port",
                value="5000",
                key=f"gnss_stream_{id}_port",
                disabled=st.session_state[f"gnss_stream_{id}_connected"]
            )
        with cols[2]:
            # Toggle connection on button press
            st.button(
                "Disconnect" if st.session_state[f"gnss_stream_{id}_connected"] else "Connect",
                key=f"connect_btn_{id}",
                on_click=lambda: {
                    st.session_state.update({
                        f"gnss_stream_{id}_connected": not st.session_state[f"gnss_stream_{id}_connected"]
                    })
                }
            )

    col1, col2 = st.columns(2)
    with col1:
        render_gnss_data_receiver(id=1)
    with col2:
        render_gnss_data_receiver(id=2)
        
@st.fragment(run_every=0.01)
def test():
    if "test_count" not in st.session_state:
        st.session_state.test_count = 0
    # st.write(f"Test count: {st.session_state.test_count}")
    print(f"Test count: {st.session_state.test_count}")
    st.session_state.test_count += 1


