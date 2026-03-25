import numpy as np
from datetime import timedelta
from models.flight import Flight, FlightStatus


def generate_delay(rng: np.random.Generator) -> int:
    """
    generates a delay in min using poisson distribution
    returns 0 if delay is not generated
    """
    if rng.random() > 0.3:
        return 0
    return int(rng.poisson(lam=20))


def apply_delay(flight: Flight, rng: np.random.Generator) -> Flight:
    """
   applies randomly generated delay to a flight
   updates actual_arrival, actual_departure, delay_minutes and status
    """

    delay = generate_delay(rng)
    flight.delay_minutes = delay

    if delay > 0:
        flight.actual_arrival = flight.scheduled_arrival + timedelta(minutes=delay)
        flight.actual_departure = flight.scheduled_departure + timedelta(minutes=delay)
        flight.status = FlightStatus.DELAYED
    else:
        flight.actual_arrival = flight.scheduled_arrival
        flight.actual_departure = flight.scheduled_departure

    return flight