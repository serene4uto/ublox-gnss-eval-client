import time
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Real-Time Data Science Dashboard",
    page_icon="✅",
    layout="wide",
)

dataset_url = "https://raw.githubusercontent.com/Lexie88rus/bank-marketing-analysis/master/bank.csv"

@st.cache_data
def get_data() -> pd.DataFrame:
    return pd.read_csv(dataset_url)

df = get_data()

st.title("Real-Time / Live Data Science Dashboard")

job_filter = st.selectbox("Select the Job", pd.unique(df["job"]))
placeholder = st.empty()
df = df[df["job"] == job_filter]

for seconds in range(200):
    # Data transformations
    df["age_new"] = df["age"] * np.random.choice(range(1, 5))
    df["balance_new"] = df["balance"] * np.random.choice(range(1, 5))
    
    # KPIs calculations
    avg_age = np.mean(df["age_new"])
    count_married = int(
        df[df["marital"] == "married"]["marital"].count()  # Fixed parenthesis
        + np.random.choice(range(1, 30))
    )
    balance = np.mean(df["balance_new"])

    with placeholder.container():
        # KPIs columns
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Age ⏳", value=round(avg_age), delta=round(avg_age)-10)
        kpi2.metric(label="Married Count 💍", value=count_married, delta=-10+count_married)
        kpi3.metric(label="A/C Balance ＄", value=f"${round(balance,2)}", delta=-round(balance/count_married)*100)

        # Chart columns
        fig_col1, fig_col2 = st.columns(2)
        with fig_col1:
            st.markdown("### First Chart")
            fig1 = px.density_heatmap(data_frame=df, y="age_new", x="marital")
            st.plotly_chart(fig1, key=f"heatmap_{seconds}")  # Added unique key
            
        with fig_col2:
            st.markdown("### Second Chart")
            fig2 = px.histogram(data_frame=df, x="age_new")
            st.plotly_chart(fig2, key=f"histogram_{seconds}")  # Added unique key

        st.markdown("### Detailed Data View")
        st.dataframe(df)
        time.sleep(0.03)
