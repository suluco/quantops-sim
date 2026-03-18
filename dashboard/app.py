import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import queue
import streamlit as st
from datetime import datetime
from simulator.engine import SimulatorEngine
from simulator.state_store import StateStore


st.set_page_config(
    page_title="QuantOps Simulator",
    layout="wide",
)

if "store" not in st.session_state:
    st.session_state.store = StateStore()
    st.session_state.event_queue = queue.Queue()
    st.session_state.engine = SimulatorEngine(
        event_queue=st.session_state.event_queue,
        sim_date=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
        state_store=st.session_state.store,
    )
    st.session_state.engine.start()

store: StateStore = st.session_state.store

st.title("✈️ QuantOps Simulator")
sim_time = store.get_sim_time()
st.caption(f"simulated time: {sim_time.strftime('%H:%M') if sim_time else 'Starting...'}")

summary = store.get_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total flights", summary["total"])
col2.metric("On time", summary["on_time"])
col3.metric("Delayed", summary["delayed"])
col4.metric("On-time %", f"{summary['on_time_pct']}%")

st.divider()

tab1, tab2 = st.tabs(["Flights", "Event log"])

with tab1:
    flights = store.get_flights()
    if flights:
        import pandas as pd
        data = [{
            "Flight": f.flight_id,
            "Airline": f.airline,
            "From": f.origin,
            "To": f.destination,
            "Scheduled arrival": f.scheduled_arrival.strftime("%H:%M"),
            "Scheduled departure": f.scheduled_departure.strftime("%H:%M"),
            "Delay (min)": f.delay_minutes,
            "Status": f.status.value,
        } for f in sorted(flights, key=lambda f: f.scheduled_arrival)]
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No flights yet...")

with tab2:
    events = store.get_events(limit=20)
    if events:
        for event in reversed(events):
            color = {"small": "🟢", "large": "🟠", "critical": "🔴"}.get(event.severity.value, "⚪")
            st.write(f"{color} `{event.timestamp.strftime('%H:%M')}` — {event.description}")
    else:
        st.info("No events yet...")

import time
time.sleep(1)
st.rerun()
