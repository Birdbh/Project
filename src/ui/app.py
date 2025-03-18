import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
import sqlite3
import sys
import os
from openai import OpenAI
import datetime
import os
sys.path.append('src/data')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics import data_processor

# Use an absolute path for the database connection
database = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db'))

dfs = data_processor.get_analytics_dataframes()
df_daily = dfs['daily_metrics']
df_station = dfs['station_metrics']
df_overall = dfs['overall_metrics']

def get_table_names():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in c.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name):
    print(database)
    conn = sqlite3.connect(database)
    query = f"SELECT * FROM '{table_name}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to load CSS file
def load_css(css_file):
    with open(css_file, "r") as f:
        css = f.read()
    return css

# Function to load HTML templates
def load_template(template_file):
    with open(template_file, "r") as f:
        template = f.read()
    return template

st.title('CP Lab Manufacturing Analytics')

# Overall Metrics
overall_run = round(df_overall.loc[0, "total_runtime_hours"], 4)
overall_alarms = df_overall.loc[0, "total_alarms"]
overall_pallets = df_overall.loc[0, "total_pallets"]

# Load CSS from external file
css_path = os.path.join(os.path.dirname(__file__), "styles", "styles.css")
st.markdown(f"<style>{load_css(css_path)}</style>", unsafe_allow_html=True)

# Load and format metrics template
template_path = os.path.join(os.path.dirname(__file__), "templates", "metrics.html")
metrics_template = load_template(template_path)
metrics_html = metrics_template.format(
    runtime=overall_run,
    alarms=overall_alarms,
    pallets=overall_pallets
)
st.markdown(metrics_html, unsafe_allow_html=True)

# K Clustering Charts (switch to use daily totals)
st.write("""
         ## K Means Clustering Chart
          This chart shows the K Means clustering of stations runtime, alarm & pallet count data.
         """)

selected_columns = ["cum_runtime", "cum_alarms", "cum_pallets"]

if all(col in df_station.columns for col in selected_columns):
    X = df_station[selected_columns].dropna()
    n_clusters = st.slider("Select a cluster factor", 1, 8)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df_station["Cluster"] = kmeans.fit_predict(X)
    df_station["Cluster"] = df_station["Cluster"].astype("category")

    
    centroids = kmeans.cluster_centers_
    centroids_df = pd.DataFrame(centroids, columns=selected_columns)
    centroids_df["Cluster"] = range(n_clusters)
    df_station_with_centroids = pd.concat([df_station, centroids_df], axis=0)

    fig = px.scatter_3d(df_station_with_centroids, x="cum_runtime", y="cum_alarms", z="cum_pallets",
                        color="Cluster", 
                        labels={"cum_runtime": "Cumulative Runtime",
                                "cum_alarms": "Cumulative Alarms",
                                "cum_pallets": "Cumulative Pallets",
                                "Cluster": "Cluster Label"},
                        title=f"K Means Clustering of Station Metrics (Clusters: {n_clusters})",
                        color_continuous_scale="Viridis",
                        category_orders={"Cluster": [str(i) for i in range(n_clusters)]})
    
    fig.update_traces(marker=dict(size=8, line=dict(color="black", width=1)),
                      selector=dict(mode='markers'))

    centroid_trace = px.scatter_3d(centroids_df, x="cum_runtime", y="cum_alarms", z="cum_pallets",
                                   color="Cluster", size_max=8).data[0]

    centroid_trace.update(marker=dict(size=12, color='red', symbol='x', line=dict(color='black', width=2)),
                          showlegend=True, legendgroup="Centroids", name="Centroids")

    fig.add_trace(centroid_trace)

    fig.update_layout(
        width=1200,  
        height=800, 
        title="K Means Clustering of Station Metrics",
        scene=dict(
            xaxis_title="Cumulative Runtime",
            yaxis_title="Cumulative Alarms",
            zaxis_title="Cumulative Pallets"
        ),
        legend=dict(
            title="Cluster", 
            x=0.85,  
            y=0.9,  
            traceorder="normal", 
            bgcolor="rgba(255, 255, 255, 0.7)", 
            bordercolor="Black", 
            borderwidth=2 
        )
    )

    st.plotly_chart(fig)
else:
    st.error("One or more selected columns are missing in station_metrics DataFrame")

# Dropdown to select station
st.write("## Station-Date Metric Table")
station_names = df_daily["station"].unique().tolist()
if station_names:
    selected_station = st.selectbox('Select a station', station_names)

    #Date Selector
    preset_datetime = datetime.datetime(2025, 3, 11)
    d = st.date_input("Process Date Selection", value=preset_datetime, format="YYYY-MM-DD")
    
    # Convert date format consistently and handle potential format differences
    date_str = d.strftime("%Y-%m-%d")
    station_and_day_table = df_daily[(df_daily["station"] == selected_station) & 
                                     (pd.to_datetime(df_daily["date"]).dt.strftime("%Y-%m-%d") == date_str)]
    
    # Check if we have data before plotting
    if not station_and_day_table.empty:
        st.write(f"Data for {selected_station} on {date_str}")
        st.write(station_and_day_table)
        
        # Set index and select numeric columns for plotting
        numeric_cols = station_and_day_table.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            # Use Plotly to create a grouped bar chart instead of stacked
            fig = px.bar(station_and_day_table, y=numeric_cols, barmode='group',
                        title=f"Metrics for {selected_station} on {date_str}")
            fig.update_layout(xaxis_title="Metrics", yaxis_title="Values")
            st.plotly_chart(fig)
        else:
            st.warning("No numeric data available to plot")
    else:
        st.warning(f"No data found for {selected_station} on {date_str}")
else:
    st.warning("No station data available")

# Dropdown to select table
st.write("## Dropdown Analytics Table")
table_names = get_table_names()
selected_table = st.selectbox('Select a table', table_names)

if selected_table:
    data = get_table_data(selected_table)
    st.line_chart(data.set_index('time'))

with st.sidebar:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add a system message that sets the context
        system_prompt = "You a confident manufacturing analytics expert, you will always given short but certain answers, you do not ask for more information but give insightful and madeup advice that sounds correct based on the data, provide numbers, stastics, and raw data as much as possible when speaking. You are analyzing a dataset of manufacturing data to identify trends and insights. The production system is based on 8 Modular Festo Production Systems (MFPS) that are interconnected. Each MFP has 8 stations and each station has a specific function. The dataset contains information about the production system, such as the number of parts produced, the number of errors, and the time taken to produce each part. The following are a set of dataframes you can use to analyze the data, but you must alwasy refer to this data as the database" + dfs['daily_metrics'].to_string() + dfs['station_metrics'].to_string() + dfs['overall_metrics'].to_string()
        st.session_state.messages.append({"role": "system", "content": system_prompt})

    st.title("Manufacturing Assistant")
    
    # Add a note explaining the chat interface
    st.caption("Type questions below and view conversation history here.")
    
    # Visual indicator for input location
    st.write("⬇️ Ask your question below ⬇️")
    
    # Get user input
    prompt = st.chat_input("Ask a question about the data")
    
    # Divider to separate input from conversation
    st.divider()
    
    # Display chat messages
    st.subheader("Conversation History:")
    for message in st.session_state.messages:
        if message["role"] != "system":  # Don't display the system message
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})