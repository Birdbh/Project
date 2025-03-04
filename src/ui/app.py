import streamlit as st
import pandas as pd
import sqlite3
import sys
sys.path.append('src/data')

import os
# Use an absolute path for the database connection
database = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db'))

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