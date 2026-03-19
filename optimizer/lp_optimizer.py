import pulp
from datetime import timedelta
from models.flight import Flight
from models.gate import Gate
from models.schedule import Schedule, TimeSlot


BUFFER_MINUTES = 15


def flights_overlap(f1: Flight, f2: Flight, buffer : int = BUFFER_MINUTES) -> bool:
    """returns True if two flights overlap in time including buffer"""
    f1_start = (f1.actual_arrival or f1.scheduled_arrival) - timedelta(minutes=buffer)
    f1_end = (f1.actual_departure or f1.scheduled_departure) + timedelta(minutes=buffer)
    f2_start = (f2.actual_arrival or f2.scheduled_arrival) - timedelta(minutes=buffer)
    f2_end = (f2.actual_departure or f2.scheduled_departure) + timedelta(minutes=buffer)
    return f1_start < f2_end and f1_end > f2_start

def assign_gates_lp(
        flights: list[Flight],
        gates: list[Gate],
        schedule: Schedule,
) -> dict[str, str | None]:
    """
    Assigns gates to flights using LP
    minimizes total gate assignments to spread load evenly
    returns a dict mapping flight_id to gate_id, or None if infeasible
    """
    prob = pulp.LpProblem("gate_assignment", pulp.LpMinimize)

    x = {
        (f.flight_id, g.gate_id): pulp.LpVariable(
            f"x_{f.flight_id}_{g.gate_id}", cat="Binary"
        )
        for f in flights
        for g in gates
    }

    prob += pulp.lpSum(x[f.flight_id, g.gate_id] for f in flights for g in gates)

    for f in flights:
        prob += pulp.lpSum(x[f.flight_id, g.gate_id] for g in gates) == 1

        for g in gates:
            for i, f1 in enumerate(flights):
                for f2 in flights[i + 1:]:
                    if flights_overlap(f1, f2):
                        prob += x[f1.flight_id, g.gate_id] + x[f2.flight_id, g.gate_id] <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    assignments: dict[str, str | None] = {}

    if pulp.LpStatus[prob.status] == "Optimal":
        for f in flights:
            for g in gates:
                if pulp.value(x[f.flight_id, g.gate_id]) == 1:
                    assignments[f.flight_id] = g.gate_id
                    f.gate_id = g.gate_id
                    slot = TimeSlot(
                        entity_id=g.gate_id,
                        flight_id=f.flight_id,
                        start_time=f.actual_arrival or f.scheduled_arrival,
                        end_time=f.actual_departure or f.scheduled_departure,
                    )
                    schedule.add_gate_slot(slot)
    else:
        for f in flights:
            assignments[f.flight_id] = None

    return assignments
    