import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
sys.path.append('src/data')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from analytics import data_processor
import os
# Use an absolute path for the database connection
database = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db'))

dfs = data_processor.get_analytics_dataframes()

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

st.title('Database Line Chart')

# Dropdown to select table
table_names = get_table_names()
selected_table = st.selectbox('Select a table', table_names)

if selected_table:
    data = get_table_data(selected_table)
    st.line_chart(data.set_index('time'))

from openai import OpenAI
import streamlit as st

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