import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    # Set page title
    st.title("📊 Simple Streamlit Dashboard Example")

    # Sidebar controls
    st.sidebar.header("Controls")
    num_points = st.sidebar.slider("Number of data points:", 5, 100, 20)
    color = st.sidebar.color_picker("Pick a color for the plot", "#1f77b4")
    show_table = st.sidebar.checkbox("Show data table", value=True)

    # Generate data
    data = {
        "X": np.arange(num_points),
        "Y": np.random.randn(num_points).cumsum()
    }
    df = pd.DataFrame(data)

    # Display selected data
    st.markdown(f"**Plotting {num_points} random data points:**")
    fig, ax = plt.subplots()
    ax.plot(df["X"], df["Y"], color=color)
    ax.set_xlabel("Index")
    ax.set_ylabel("Cumulative Sum")
    st.pyplot(fig)

    if show_table:
        st.dataframe(df)

if __name__ == "__main__":
    main()
