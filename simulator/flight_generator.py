import numpy as np
from datetime import datetime, timedelta
from models.flight import Flight, FlightStatus
import random


AIRLINES = ["KLM", "Transavia", "Ryanair", "Lufthansa", "British Airways", "Easyjet"]

#schengen destinations -> terminal D
#non-schengen destinations -> terminal E/F
SCHENGEN_DESTINATIONS = ["CDG", "FRA", "BCN", "MAD", "BRU", "ZRH", "VIE", "FCO"]
NON_SCHENGEN_DESTINATIONS = ["LHR", "JFK", "DXB", "BKK", "YYZ", "GRU"]

DESTINATIONS = SCHENGEN_DESTINATIONS + NON_SCHENGEN_DESTINATIONS


def generate_flight_id(airline: str) -> str:
    """generates a random flight id based on airline code"""
    code = airline[:2].upper()
    number = random.randint(100, 999)
    return f"{code}{number}"


def generate_flights(date: datetime, n: int = 50) -> list[Flight]:
    """
    generates n flights for a given date with realistic time distibrution.
    uses peak hours (07-09, 17-19) and off-peak hours for scheduling
    """
    rng = np.random.default_rng(seed=42)
    flights = []

    # peak hours het 60% of total flights
    peak_slots = int(n * 0.6)
    offpeak_slots = n - peak_slots

    def random_peak_time() -> datetime:
        peak_windows = [(7, 9), (17, 19)]
        window = random.choice(peak_windows)
        hour = rng.integers(window[0], window[1])
        minute = rng.integers(0, 60)
        return date.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    
    def random_offpeak_time() -> datetime:
        if rng.random() < 0.7:
            hour = rng.integers(10, 17)
            minute = rng.integers(0, 60)
        else:
            hour = 19 + int(rng.random() < 0.5)
            minute = rng.integers(0, 30) if hour == 20 else rng.integers(0, 60)
        return date.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    
    for i in range(n):
        airline = random.choice(AIRLINES)

        #70% Schengen, 30% non-Schengen
        if rng.random() < 0.7:
            other_airport = random.choice(SCHENGEN_DESTINATIONS)
        else:
            other_airport = random.choice(NON_SCHENGEN_DESTINATIONS)

        if rng.random() < 0.5:
            origin = other_airport
            destination = "AMS"
        else:
            origin = "AMS"
            destination = other_airport

        arrival = random_peak_time() if i < peak_slots else random_offpeak_time()
        turnaround = timedelta(minutes=int(rng.integers(45, 76)))
        departure = arrival + turnaround

        flight = Flight(
            flight_id=generate_flight_id(airline),
            airline=airline,
            origin=origin,
            destination=destination,
            scheduled_arrival=arrival,
            scheduled_departure=departure,
            passenger_count=int(rng.integers(80, 200))
        )
        flights.append(flight)

    flights.sort(key=lambda f: f.scheduled_arrival)
    return flights

