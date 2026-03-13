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
