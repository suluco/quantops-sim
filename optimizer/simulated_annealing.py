import random
import math
from datetime import timedelta
from models.flight import Flight
from models.gate import Gate
from models.schedule import Schedule, TimeSlot


BUFFER_MINUTES = 15


def _build_schedule(
    assignments: dict[str, str],
    flights: list[Flight],
    gates: list[Gate],
) -> Schedule:
    """builds a Schedule object from a flight-to-gate assignment dict"""
    schedule = Schedule()
    gate_map = {g.gate_id: g for g in gates}
    flight_map = {f.flight_id: f for f in flights}

    for flight_id, gate_id in assignments.items():
        flight = flight_map[flight_id]
        gate = gate_map[gate_id]
        slot = TimeSlot(
            entity_id=gate.gate_id,
            flight_id=flight.flight_id,
            start_time=flight.actual_arrival or flight.scheduled_arrival,
            end_time=flight.actual_departure or flight.scheduled_departure,
        )
        schedule.add_gate_slot(slot)

    return schedule


def _count_conflicts(assignments: dict[str, str], flights: list[Flight]) -> int:
    """counts conflicts in a given assignment dict"""
    gate_flights: dict[str, list[Flight]] = {}
    flight_map = {f.flight_id: f for f in flights}

    for flight_id, gate_id in assignments.items():
        gate_flights.setdefault(gate_id, []).append(flight_map[flight_id])

    conflicts = 0
    for gate_id, gate_flight_list in gate_flights.items():
        for i, f1 in enumerate(gate_flight_list):
            for f2 in gate_flight_list[i + 1:]:
                f1_start = (f1.actual_arrival or f1.scheduled_arrival) - timedelta(minutes=BUFFER_MINUTES)
                f1_end = (f1.actual_departure or f1.scheduled_departure) + timedelta(minutes=BUFFER_MINUTES)
                f2_start = (f2.actual_arrival or f2.scheduled_arrival) - timedelta(minutes=BUFFER_MINUTES)
                f2_end = (f2.actual_departure or f2.scheduled_departure) + timedelta(minutes=BUFFER_MINUTES)
                if f1_start < f2_end and f1_end > f2_start:
                    conflicts += 1

    return conflicts


def assign_gates_sa(
    flights: list[Flight],
    gates: list[Gate],
    schedule: Schedule,
    max_iterations: int = 1000,
    initial_temp: float = 100.0,
    cooling_rate: float = 0.95,
) -> dict[str, str | None]:
    """
    assigns gates to flights using Simulated Annealing
    starts with a random assignment and iteratively improves it
    returns a dict mapping flight_id to gate_id
    """
    gate_ids = [g.gate_id for g in gates]

    current = {f.flight_id: random.choice(gate_ids) for f in flights}
    best = current.copy()
    best_conflicts = _count_conflicts(best, flights)
    temp = initial_temp

    for _ in range(max_iterations):
        candidate = current.copy()
        flight_id = random.choice(list(candidate.keys()))
        candidate[flight_id] = random.choice(gate_ids)

        current_conflicts = _count_conflicts(current, flights)
        candidate_conflicts = _count_conflicts(candidate, flights)
        delta = candidate_conflicts - current_conflicts

        if delta < 0 or random.random() < math.exp(-delta / max(temp, 0.001)):
            current = candidate

        if candidate_conflicts < best_conflicts:
            best = candidate.copy()
            best_conflicts = candidate_conflicts

        temp *= cooling_rate

        if best_conflicts == 0:
            break

    flight_map = {f.flight_id: f for f in flights}
    for flight_id, gate_id in best.items():
        flight_map[flight_id].gate_id = gate_id

    for flight_id, gate_id in best.items():
        flight = flight_map[flight_id]
        slot = TimeSlot(
            entity_id=gate_id,
            flight_id=flight_id,
            start_time=flight.actual_arrival or flight.scheduled_arrival,
            end_time=flight.actual_departure or flight.scheduled_departure,
        )
        schedule.add_gate_slot(slot)

    return {fid: gid for fid, gid in best.items()}