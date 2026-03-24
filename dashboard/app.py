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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Flights", "Event log", "Gantt", "Scenario", "Comparison", "Map"])

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

        import io
        csv_buffer = io.StringIO()
        pd.DataFrame(data).to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download planning as CSV",
            data=csv_buffer.getvalue(),
            file_name=f"quantops_planning_{sim_date.strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
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
            "Gate": f.gate_id if f.status.value != "cancelled" or (f.actual_arrival or f.scheduled_arrival) <= (store.get_sim_time() or datetime.now()) else "Cancelled",
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
        fig.update_traces(
            opacity=0.4,
            selector=dict(name="cancelled")
        )
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

with tab4:
    st.subheader("Inject a scenario")
    flights = store.get_flights()

    if not flights:
        st.info("No flights available yet...")
    else:
        flight_ids = [f.flight_id for f in sorted(flights, key=lambda f: f.scheduled_arrival)]

        col1, col2 = st.columns(2)
        with col1:
            selected_flight_id = st.selectbox("Select flight", flight_ids)
            scenario_type = st.selectbox("Scenario type", ["Delay", "Cancel", "Maintenance"])
        
        with col2:
            if scenario_type == "Delay":
                delay_minutes = st.slider("Delay (minutes)", min_value=5, max_value=180, value=30, step=5)
            st.write("")
            st.write("")
            inject = st.button("Inject scenario")
        
        if inject:
            from datetime import timedelta
            from models.event import Event, EventType, EventSeverity
            from simulator.event_generator import create_delay_event, create_cancel_event, create_maintenance_event
            import uuid

            flight = next(f for f in flights if f.flight_id == selected_flight_id)
            sim_time = store.get_sim_time() or datetime.now()

            if scenario_type == "Delay":
                flight.delay_minutes += delay_minutes
                if flight.actual_arrival:
                    flight.actual_arrival += timedelta(minutes=delay_minutes)
                if flight.actual_departure:
                    flight.actual_departure += timedelta(minutes=delay_minutes)
                else:
                    flight.actual_departure = flight.scheduled_departure + timedelta(minutes=delay_minutes)
                if flight.actual_arrival is None:
                    flight.actual_arrival = flight.scheduled_arrival + timedelta(minutes=delay_minutes)
                from models.flight import FlightStatus
                flight.status = FlightStatus.DELAYED
                store.update_flight(flight)
                event = create_delay_event(flight, sim_time)
                store.add_event(event)
                st.session_state.event_queue.put(event)
                st.session_state.optimizer.force_replan()
                st.success(f"Flight {selected_flight_id} delayed by {delay_minutes} minutes")
            
            elif scenario_type == "Cancel":
                event = create_cancel_event(flight, sim_time)
                store.add_event(event)
                store.update_flight(flight)
                st.session_state.event_queue.put(event)
                st.session_state.optimizer.force_replan()
                st.success(f"Flight {selected_flight_id} canceled")
            
            elif scenario_type == "Maintenance":
                gate_id = flight.gate_id or "unknown"
                event = create_maintenance_event(gate_id, sim_time)
                store.add_event(event)
                st.session_state.event_queue.put(event)
                st.session_state.optimizer.force_replan()
                st.warning(f"Gate {gate_id} taken out of service")


with tab5:
    import json
    benchmark_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'benchmark_results.json')
    
    if os.path.exists(benchmark_path):
        with open(benchmark_path) as f:
            bench = json.load(f)

        algos = list(bench.keys())
        times = [bench[a]["avg_time_ms"] for a in algos]
        conflicts = [bench[a]["avg_conflicts"] for a in algos]
        distribution = [bench[a]["avg_distribution"] for a in algos]

        st.subheader("Algorithm Comparison")
        st.caption("Based on 5 benchmark runs with 20 flights each")

        col1, col2, col3 = st.columns(3)

        with col1:
            fig_time = px.bar(
                x=algos, y=times,
                labels={"x": "Algorithm", "y": "Avg time (ms)"},
                title="Execution time",
                color=algos,
                color_discrete_sequence=["#2ecc71", "#e67e22", "#3498db", "#9b59b6"],
            )
            fig_time.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_time, use_container_width=True)

        with col2:
            fig_conf = px.bar(
                x=algos, y=conflicts,
                labels={"x": "Algorithm", "y": "Avg conflicts remaining"},
                title="Conflicts remaining",
                color=algos,
                color_discrete_sequence=["#2ecc71", "#e67e22", "#3498db", "#9b59b6"],
            )
            fig_conf.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(range=[0, 5]))
            st.plotly_chart(fig_conf, use_container_width=True)

        with col3:
            fig_dist = px.bar(
                x=algos, y=distribution,
                labels={"x": "Algorithm", "y": "Distribution std (lower = better)"},
                title="Gate distribution",
                color=algos,
                color_discrete_sequence=["#2ecc71", "#e67e22", "#3498db", "#9b59b6"],
            )
            fig_dist.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_dist, use_container_width=True)

        st.divider()
        st.subheader("Raw results")
        bench_data = [{
            "Algorithm": a,
            "Avg time (ms)": bench[a]["avg_time_ms"],
            "Avg conflicts": bench[a]["avg_conflicts"],
            "Gate distribution std": bench[a]["avg_distribution"],
        } for a in algos]
        st.dataframe(bench_data, use_container_width=True)
    else:
        st.info("No benchmark results found. Run `python -m optimizer.benchmark` first.")


with tab6:
    from dashboard.live_map import build_live_map
    from simulator.vehicle_generator import generate_vehicles

    flights = store.get_flights()
    sim_time_now = store.get_sim_time()

    #generate vehicles if not in session state
    if "vehicles" not in st.session_state:
        st.session_state.vehicles = generate_vehicles()

    #assign vehicles to gates based on current flights
    vehicles = st.session_state.vehicles
    for vehicle in vehicles:
        vehicle.current_gate_id = None
    for flight in flights:
        if flight.gate_id and (flight.actual_arrival or flight.scheduled_arrival) <= (sim_time_now or datetime.now()):
            for vehicle in vehicles:
                if vehicle.current_gate_id is None and vehicle.is_available:
                    vehicle.current_gate_id = flight.gate_id
                    break

    if sim_time_now:
        fig_live = build_live_map(flights, vehicles, sim_time_now)
        st.plotly_chart(fig_live, use_container_width=True)
    else:
        st.info("Simulator starting...")

time.sleep(3)
st.rerun()