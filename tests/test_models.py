import numpy as np
from datetime import datetime
from models.flight import Flight, FlightStatus
from models.gate import Gate, GateType
from models.ground_vehicle import GroundVehicle, VehicleType
from models.event import Event, EventType, EventSeverity
from models.schedule import Schedule, TimeSlot

def test_flight_turnaround():
    flight = Flight(
        flight_id="KL123",
        airline="KLM",
        origin="AMS",
        destination="LHR",
        scheduled_arrival=datetime(2026, 3, 13, 8, 0),
        scheduled_departure=datetime(2026, 3, 13, 9, 30),
    )
    assert flight.turnaround_minutes() == 90
    assert flight.is_delayed() is False


def test_gate_assign_and_release():
    gate = Gate(gate_id="A1", terminal="A", gate_type=GateType.SCHENGEN)
    gate.assign_flight("KL13")
    assert gate.is_available is False
    gate.release()
    assert gate.is_available is True


def test_schedule_conflict_detection():
    schedule = Schedule()
    slot_a = TimeSlot("A1", "KL123", datetime(2026, 3, 13, 8, 0), datetime(2026, 3, 13, 9, 30))
    slot_b = TimeSlot("A1", "KL456", datetime(2026, 3, 13, 9, 0), datetime(2026, 3, 13, 10, 0))
    schedule.add_gate_slot(slot_a)
    schedule.add_gate_slot(slot_b)
    conflicts = schedule.get_conflicts()
    assert len(conflicts) == 1


from simulator.flight_generator import generate_flights

def test_flight_generator():
    date = datetime(2026, 3 ,13)
    flights = generate_flights(date, n=50)

    assert len(flights) ==50
    assert all(f.scheduled_departure > f.scheduled_arrival for f in flights)
    assert all(f.turnaround_minutes() >= 45 for f in flights)
    #check sorted by arrival
    arrivals = [f.scheduled_arrival for f in flights]
    assert arrivals == sorted(arrivals)
    


from simulator.statistics import flights_per_hour, average_turnaround, peak_hour_ratio

def test_statistics():
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=50)

    assert average_turnaround(flights) > 0
    assert 0.0 <= peak_hour_ratio(flights) <= 1.0
    per_hour = flights_per_hour(flights)
    assert sum(per_hour.values()) == 50



from simulator.delay_model import generate_delay, apply_delay

def test_delay_model():
    rng = np.random.default_rng(seed=42)
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=100)

    delayed = [apply_delay(f, rng) for f in flights]

    n_delayed = sum(1 for f in delayed if f.is_delayed())
    assert 0 < n_delayed < 100

    for f in delayed:
        if f.is_delayed():
            assert f.actual_arrival > f.scheduled_arrival
            assert f.delay_minutes > 0




from simulator.event_generator import (
    create_delay_event, create_cancel_event,
    create_maintenance_event, create_gate_change_event, classify_severity
)
from models.event import EventType, EventSeverity

def test_event_generator():
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=10)
    rng = np.random.default_rng(seed=42)
    flight = apply_delay(flights[0], rng)

    event = create_delay_event(flight, date)
    assert event.event_type == EventType.DELAY
    assert event.entity_id == flight.flight_id


    cancel = create_cancel_event(flights[1], date)
    assert cancel.event_type == EventType.CANCEL
    assert cancel.severity == EventSeverity.CRITICAL


    assert classify_severity(5) == EventSeverity.SMALL
    assert classify_severity(20) == EventSeverity.LARGE
    assert classify_severity(60) == EventSeverity.CRITICAL



import time
import queue
from simulator.engine import SimulatorEngine

def test_simulator_engine():
    event_queue = queue.Queue()
    sim_date = datetime (2026, 3, 13)
    engine = SimulatorEngine(event_queue, sim_date)

    engine.start()
    time.sleep(5)
    engine.stop()


    assert not event_queue.empty()


    event = event_queue.get()
    assert event.entity_id is not None
    assert event.timestamp is not None



from simulator.state_store import StateStore

def test_state_store():
    event_queue = queue.Queue()
    sim_date = datetime(2026, 3, 13)
    store = StateStore()
    engine = SimulatorEngine(event_queue, sim_date, state_store=store)

    engine.start()
    time.sleep(5)
    engine.stop()


    flights = store.get_flights()
    assert len(flights) >= 48

    events = store.get_events()
    assert len(events) > 0

    summary = store.get_summary()
    assert summary["total"] >= 48
    assert summary["on_time_pct"] >= 0.0
    


from simulator.gate_generator import generate_gates
from optimizer.greedy import assign_gates_greedy

def test_greedy_optimizer():
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=50)
    rng = np.random.default_rng(seed=42)
    for flight in flights:
        apply_delay(flight, rng)
    
    gates = generate_gates()
    schedule = Schedule()
    assignments = assign_gates_greedy(flights, gates, schedule)

    assert len(assignments) >= 48
    assert all(gate_id is not None for gate_id in assignments.values())

    conflicts = schedule.get_conflicts()
    assert len(conflicts) == 0



from optimizer.conflict_detector import count_conflicts, classify_conflict_severity, get_conflicting_flights

def test_conflict_detector():
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=50)
    rng = np.random.default_rng(seed=42)
    for flight in flights:
        apply_delay(flight, rng)
    
    gates = generate_gates()
    schedule = Schedule()
    assign_gates_greedy(flights, gates, schedule)

    assert count_conflicts(flights, schedule) == 0

    assert classify_conflict_severity(0, 50) == "none"
    assert classify_conflict_severity(2, 50) == "small"
    assert classify_conflict_severity(5, 50) == "large"
    assert classify_conflict_severity(25, 50) == "cascade"

    conflicting = get_conflicting_flights(flights, schedule)
    assert len(conflicting) == 0 



from optimizer.lp_optimizer import assign_gates_lp

def test_lp_optimizer():
    date = datetime(2026, 3, 13)
    flights = generate_flights(date, n=20)
    rng = np.random.default_rng(seed=42)
    for flight in flights:
        apply_delay(flight, rng)

    gates = generate_gates()
    schedule = Schedule()
    assignments = assign_gates_lp(flights, gates, schedule)

    assert len(assignments) == 20
    assert all(gate_id is not None for gate_id in assignments.values())

    conflicts = schedule.get_conflicts()
    assert len(conflicts) == 0



from optimizer.engine import OptimizerEngine

def test_optimizer_engine():
    event_queue = queue.Queue()
    sim_date = datetime(2026, 3, 13)
    store = StateStore()
    gates = generate_gates()

    simulator = SimulatorEngine(event_queue, sim_date, state_store=store)
    optimizer = OptimizerEngine(event_queue, store, gates)

    simulator.start()
    optimizer.start()
    time.sleep(5)
    optimizer.stop()
    simulator.stop()

    flights = store.get_flights()
    assert all(f.gate_id is not None for f in flights)