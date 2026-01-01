import streamlit as st
import pandas as pd
import json
import time
import os

# Page Config
st.set_page_config(
    page_title="LLM Cost & Performance Tracker",
    page_icon="📊",
    layout="wide"
)

LOG_FILE = os.getenv("LOG_FILE", "request_logs.jsonl")

def load_data():
    """
    Reads the JSONL log file and converts it to a Pandas DataFrame.
    """
    data = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return pd.DataFrame()
        
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    # Convert timestamp to datetime object
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

# --- Main Dashboard Layout ---

st.title("🔥 LLM Middleware Observability")
st.markdown("Real-time metrics from your local Ollama wrapper.")

# Auto-refresh button
if st.button('🔄 Refresh Data'):
    st.rerun()

df = load_data()

if df.empty:
    st.warning("No logs found yet. Make some requests to the API!")
else:
    # --- Top Level Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_reqs = len(df)
    total_cost = df['cost_usd'].sum()
    avg_latency = df['latency_ms'].mean()
    # Calculate savings (Hypothetical: if everything was 'llama3')
    # Assuming llama3 input is 5x more expensive than llama3-mini
    theoretical_max_cost = total_cost * 1.5 # Placeholder logic for demo
    savings = theoretical_max_cost - total_cost

    col1.metric("Total Requests", total_reqs)
    col2.metric("Total Cost (Est)", f"${total_cost:.4f}")
    col3.metric("Avg Latency", f"{avg_latency:.0f} ms")
    col4.metric("Est. Savings", f"${savings:.4f}", delta_color="normal")

    st.divider()

    # --- Charts Row 1 ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🤖 Model Routing Distribution")
        # Pie chart of models used
        model_counts = df['model'].value_counts()
        st.bar_chart(model_counts)
        st.caption("How often is the Router selecting the Small vs Large model?")

    with c2:
        st.subheader("⏱️ Latency Over Time")
        # Line chart of latency
        st.line_chart(df.set_index('timestamp')['latency_ms'])
        st.caption("Spikes indicate heavy load or complex queries.")

    st.divider()
    
    # --- Raw Data Table ---
    st.subheader("📝 Recent Logs")
    # Show last 10 requests, newest first
    st.dataframe(
        df.sort_values(by="timestamp", ascending=False).head(10)[
            ["timestamp", "model", "complexity_score", "input_tokens", "output_tokens", "latency_ms", "cost_usd"]
        ],
        use_container_width=True
    )