import streamlit as st
import pandas as pd
import numpy as np
import time

st.title('Real-time Data Update')

# Create a placeholder for the graph
graph_placeholder = st.empty()

# Generate random data
data = pd.DataFrame(np.random.randn(10, 2), columns=['x', 'y'])

# Update the graph
graph_placeholder.line_chart(data)

# Wait for 2 seconds before rerunning
time.sleep(2)

# Rerun the script
st.rerun()