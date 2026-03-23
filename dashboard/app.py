import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import queue
import streamlit as st
from datetime import datetime
from simulator.engine import SimulatorEngine
from simulator.state_store import StateStore
import plotly.express as px
import pandas as pd
import time

st.set_page_config(page_title="QuantOps Simulator", layout="wide")

if "store" not in st.session_state:
    from simulator.gate_generator import generate_gates
    from optimizer.engine import OptimizerEngine

    st.session_state.store = StateStore()
    st.session_state.event_queue = queue.Queue()
    st.session_state.gates = generate_gates()
    st.session_state.engine = SimulatorEngine(
        event_queue=st.session_state.event_queue,
        sim_date=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
        state_store=st.session_state.store,
    )
    st.session_state.optimizer = OptimizerEngine(
        event_queue=st.session_state.event_queue,
        state_store=st.session_state.store,
        gates=st.session_state.gates,
    )
    st.session_state.engine.start()
    st.session_state.optimizer.start()

store: StateStore = st.session_state.store
sim_date = st.session_state.engine.sim_date

st.title("✈️ QuantOps Simulator")
sim_time = store.get_sim_time()
st.caption(f"Simulated time: {sim_time.strftime('%H:%M') if sim_time else 'Starting...'} — {sim_date.strftime('%d-%m-%Y')}")

summary = store.get_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total flights", summary["total"])
col2.metric("On time", summary["on_time"])
col3.metric("Delayed", summary["delayed"])
col4.metric("On-time %", f"{summary['on_time_pct']}%")

st.divider()

tab1, tab2, tab3 = st.tabs(["Flights", "Event log", "Gantt"])

with tab1:
    flights = store.get_flights()
    if flights:
        data = [{
            "Flight": f.flight_id,
            "Airline": f.airline,
            "From": f.origin,
            "To": f.destination,
            "Gate": f.gate_id or "—",
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

with tab3:
    flights = store.get_flights()
    assigned = [f for f in flights if f.gate_id]

    active_weather = None
    sim_time_now = store.get_sim_time()
    if sim_time_now:
        from simulator.weather import get_active_weather
        active_weather = get_active_weather(
            st.session_state.engine.weather_events, sim_time_now
        )
    if active_weather:
        st.warning(f"Actief weer: **{active_weather.weather_type.value.upper()}** — delay factor {active_weather.delay_factor}x")
    else:
        st.success("Geen actief weer")

    if assigned:
        assigned_sorted = sorted(assigned, key=lambda f: f.gate_id or "")

        gantt_data = [{
            "Gate": f.gate_id,
            "Flight": f.flight_id,
            "Start": (f.actual_arrival or f.scheduled_arrival).isoformat(),
            "Finish": (f.actual_departure or f.scheduled_departure).isoformat(),
            "Status": f.status.value,
        } for f in assigned_sorted]

        df = pd.DataFrame(gantt_data)
        color_map = {
            "scheduled": "#2ecc71",
            "delayed": "#e67e22",
            "cancelled": "#e74c3c",
            "boarding": "#3498db",
            "departed": "#95a5a6",
        }
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Gate",
            color="Status",
            text="Flight",
            hover_name="Flight",
            color_discrete_map=color_map,
            title="Gate planning — today",
        )
        fig.update_yaxes(autorange="reversed", tickfont=dict(size=12))
        fig.update_traces(textposition="inside", insidetextanchor="middle")
        fig.update_xaxes(tickformat="%H:%M", tickfont=dict(size=11))
        fig.update_layout(
            height=700,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            bargap=0.2,
            bargroupgap=0.1,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nog geen gate-toewijzingen...")

time.sleep(3)
st.rerun()