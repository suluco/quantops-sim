from datetime import timedelta
from models.flight import Flight
from models.schedule import Schedule


BUFFER_MINUTES = 15


def find_cascade(
        delayed_flight: Flight,
        all_flights: list[Flight],
        schedule: Schedule,
) -> list[Flight]:
    """
    finds all flights affected by a cascade from a delayed flight
    a flight is affected when it shares a gate and its arrival overlaps
    with the delayed flights new dep time
    """
    affected: list[Flight] = []
    if not delayed_flight.gate_id:
        return affected
    
    delayed_departure = delayed_flight.actual_departure or delayed_flight.scheduled_departure

    for flight in all_flights:
        if flight.flight_id == delayed_flight.flight_id:
            continue
        if flight.gate_id != delayed_flight.gate_id:
            continue

        flight_arrival = flight.actual_arrival or flight.scheduled_arrival
        if flight_arrival < delayed_departure + timedelta(minutes=BUFFER_MINUTES):
            affected.append(flight)

    return affected


def apply_cascade(
        delayed_flight: Flight,
        all_flights: list[Flight],
        schedule: Schedule,
) -> list[Flight]:
    """
    applies cascade delays to all affected flights
    each affected flight inherits the delay of the triggering flight
    returns the list of flights that were affected
    """
    from datetime import timedelta
    affected = find_cascade(delayed_flight, all_flights, schedule)

    for flight in affected:
        extra = delayed_flight.delay_minutes
        if extra > 0:
            flight.delay_minutes += extra
            if flight.actual_arrival:
                flight.actual_arrival += timedelta(minutes=extra)
            if flight.actual_departure:
                flight.actual_departure += timedelta(minutes=extra)
    
    return affected


def cascade_ratio(all_flights: list[Flight], affected: list[Flight]) -> float:
    """returns ratio of cascade-affected flights vs tot flights"""
    if not all_flights:
        return 0.0
    return len(affected) / len(all_flights)