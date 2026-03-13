from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FlightStatus(Enum):
    SCHEDULED = "scheduled"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    BOARDING = "boarding"
    DEPARTED = "departed"


@dataclass
class Flight:
    """Represents a commercial flight in the simulation."""

    flight_id: str
    airline: str
    origin: str
    destination: str
    scheduled_arrival: datetime
    scheduled_departure: datetime
    actual_arrival: datetime | None = None
    actual_departure: datetime | None = None
    gate_id: str | None = None
    status: FlightStatus = FlightStatus.SCHEDULED
    delay_minutes: int = 0
    passenger_count: int = 0

    def is_delayed(self) -> bool:
        """Returns Ture if the flight has a delay."""
        return self.delay_minutes > 0
    
    def turnaround_minutes(self) -> int:
        """Returns the scheduled turnaround time in minutes."""
        delta = self.scheduled_departure - self.scheduled_arrival
        return int(delta.total_seconds() / 60)
    
