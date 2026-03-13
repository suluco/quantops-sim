from dataclasses import dataclass, field
from enum import Enum


class GateType(Enum):
    SCHENGEN = "schengen"
    NON_SCHENGEN = "non_schengen"
    DOMESTIC = "domestic"



@dataclass
class Gate:
    """Represents an airport gate in the sim."""

    gate_id: str
    terminal: str
    gate_type: GateType
    capacity: int = 200
    is_available: bool = True
    current_flight_id: str | None = None

    def assign_flight(self, flight_id: str) -> None:
        """Assigns a flight to this gate"""
        self.current_flight_id = flight_id
        self.is_available = False

    def release(self) -> None:
        """Releases the gate after flight has departed."""
        self.current_flight_id = None
        self.is_available = True
            