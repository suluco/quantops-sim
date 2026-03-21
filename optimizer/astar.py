import heapq
from datetime import timedelta
from models.flight import Flight
from models.gate import Gate
from models.schedule import Schedule, TimeSlot


BUFFER_MINUTES = 15


def _slot_conflicts(
    flight: Flight,
    gate_id: str,
    assigned: dict[str, list[Flight]],
) -> int:
    """counts how many conflicts assigning flight to gate_id would create"""
    conflicts = 0
    for existing in assigned.get(gate_id, []):
        f1_start = (flight.actual_arrival or flight.scheduled_arrival) - timedelta(minutes=BUFFER_MINUTES)
        f1_end = (flight.actual_departure or flight.scheduled_departure) + timedelta(minutes=BUFFER_MINUTES)
        f2_start = (existing.actual_arrival or existing.scheduled_arrival) - timedelta(minutes=BUFFER_MINUTES)
        f2_end = (existing.actual_departure or existing.scheduled_departure) + timedelta(minutes=BUFFER_MINUTES)
        if f1_start < f2_end and f1_end > f2_start:
            conflicts += 1
    return conflicts


def assign_gates_astar(
    flights: list[Flight],
    gates: list[Gate],
    schedule: Schedule,
) -> dict[str, str | None]:
    """
    assigns gates to flights using A* search
    processes flights in order of arrival time
    uses conflicts as cost and remaining unassigned flights as heuristic
    returns a dict mapping flight_id to gate_id, or None if no gate found
    """
    sorted_flights = sorted(
        flights, key=lambda f: f.actual_arrival or f.scheduled_arrival
    )

    counter = 0
    initial: tuple = (0, counter, 0, {}, {g.gate_id: [] for g in gates})
    heap = [initial]
    gate_ids = [g.gate_id for g in gates]

    best_assignments: dict[str, str | None] = {}
    best_cost = float("inf")

    visited = 0
    max_visits = 5000  

    while heap and visited < max_visits:
        cost, _, idx, assignments, assigned_map = heapq.heappop(heap)
        visited += 1

        if idx == len(sorted_flights):
            if cost < best_cost:
                best_cost = cost
                best_assignments = assignments.copy()
            continue

        flight = sorted_flights[idx]

        for gate_id in gate_ids:
            conflicts = _slot_conflicts(flight, gate_id, assigned_map)
            new_cost = cost + conflicts
            new_assignments = assignments | {flight.flight_id: gate_id}
            new_assigned_map = {
                gid: list(flist) for gid, flist in assigned_map.items()
            }
            new_assigned_map[gate_id].append(flight)
            heuristic = len(sorted_flights) - idx - 1
            counter += 1
            heapq.heappush(heap, (new_cost + heuristic, counter, idx + 1, new_assignments, new_assigned_map))

    flight_map = {f.flight_id: f for f in flights}
    for flight_id, gate_id in best_assignments.items():
        flight = flight_map[flight_id]
        flight.gate_id = gate_id
        slot = TimeSlot(
            entity_id=gate_id,
            flight_id=flight_id,
            start_time=flight.actual_arrival or flight.scheduled_arrival,
            end_time=flight.actual_departure or flight.scheduled_departure,
        )
        schedule.add_gate_slot(slot)

    if not best_assignments:
        from optimizer.greedy import assign_gates_greedy
        fallback_schedule = Schedule()
        best_assignments = assign_gates_greedy(flights, gates, fallback_schedule)
        for flight_id, gate_id in best_assignments.items():
            if gate_id:
                flight = flight_map[flight_id]
                slot = TimeSlot(
                    entity_id=gate_id,
                    flight_id=flight_id,
                    start_time=flight.actual_arrival or flight.scheduled_arrival,
                    end_time=flight.actual_departure or flight.scheduled_departure,
                )
                schedule.add_gate_slot(slot)

    return best_assignments