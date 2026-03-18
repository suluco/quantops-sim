from datetime import datetime, timedelta
from models.flight import Flight
from models.gate import Gate
from models.schedule import Schedule, TimeSlot


def find_available_gate(
        flight: Flight,
        gates: list[Gate],
        schedule: Schedule,
        buffer_minutes: int = 15,
) -> Gate | None:
    """
    finds the first avail gate for a flight using greedy strategy.
    adds buffer between flights to allow cleaning and boarding.
    returns None if no gate is avail.
    """
    arrival = flight.actual_arrival or flight.scheduled_arrival
    departure = flight.actual_departure or flight.scheduled_departure
    slot = TimeSlot(
        entity_id="",
        flight_id=flight.flight_id,
        start_time=arrival - timedelta(minutes=buffer_minutes),
        end_time=departure + timedelta(minutes=buffer_minutes),
    )

    for gate in gates: 
        existing_slots = schedule.gate_slots.get(gate.gate_id, [])
        conflict = any(slot.overlaps_with(s) for s in existing_slots)
        if not conflict:
            return gate
        
    return None


def assign_gates_greedy(
        flights: list[Flight],
        gates: list[Gate],
        schedule: Schedule,
) -> dict[str, str | None]:
    """
    assigns gates to all flights using greedy first-fit strat
    sorts flights by arrival time and assigns each to first avail gate
    returns a dict mapping flight_id to gate_id or None if no gate found
    """
    assignments: dict[str, str | None] ={}
    sorted_flights = sorted(
        flights, key=lambda f: f.actual_arrival or f.scheduled_arrival   
    )

    for flight in sorted_flights:
        gate = find_available_gate(flight, gates, schedule)
        if gate:
            arrival = flight.actual_arrival or flight.scheduled_arrival
            departure = flight.actual_departure or flight.scheduled_departure
            slot = TimeSlot(
                entity_id=gate.gate_id,
                flight_id=flight.flight_id,
                start_time=arrival,
                end_time=departure,
            )
            schedule.add_gate_slot(slot)
            gate.assign_flight(flight.flight_id)
            flight.gate_id = gate.gate_id
            assignments[flight.flight_id] = gate.gate_id
        else:
            assignments[flight.flight_id] = None
    
    return assignments