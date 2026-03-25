import uuid
from datetime import datetime
from models.event import Event, EventType, EventSeverity
from models.flight import Flight, FlightStatus


def classify_severity(delay_minutes: int) -> EventSeverity:
    """classifies event severity based on delay duration in min"""
    if delay_minutes < 15:
        return EventSeverity.SMALL
    elif delay_minutes < 45:
        return EventSeverity.LARGE
    return EventSeverity.CRITICAL


def create_delay_event(flight: Flight, timestamp: datetime) -> Event:
    """creates a DELAY event for a given flight"""
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.DELAY,
        severity=classify_severity(flight.delay_minutes),
        timestamp=timestamp,
        entity_id=flight.flight_id,
        description=f"Flight {flight.flight_id} delayed by {flight.delay_minutes}min",
    )


def create_cancel_event(flight: Flight, timestamp: datetime) -> Event:
    """Creates a CANCEL event and updates flight status."""
    flight.status = FlightStatus.CANCELLED
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.CANCEL,
        severity=EventSeverity.CRITICAL,
        timestamp=timestamp,
        entity_id=flight.flight_id,
        description=f"Flight {flight.flight_id} cancelled",
    )


def create_maintenance_event(gate_id: str, timestamp: datetime) -> Event:
    """Creates a MAINTENANCE event for a given gate."""
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.MAINTENANCE,
        severity=EventSeverity.LARGE,
        timestamp=timestamp,
        entity_id=gate_id,
        description=f"Gate {gate_id} taken out of service for maintenance",
    )


def create_gate_change_event(flight: Flight, new_gate_id: str, timestamp: datetime) -> Event:
    """Creates a GATE_CHANGE event and updates the flight's gate."""
    old_gate = flight.gate_id
    flight.gate_id = new_gate_id
    return Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.GATE_CHANGE,
        severity=EventSeverity.SMALL,
        timestamp=timestamp,
        entity_id=flight.flight_id,
        description=f"Flight {flight.flight_id} moved from gate {old_gate} to {new_gate_id}",
    )