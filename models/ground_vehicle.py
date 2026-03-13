from dataclasses import dataclass
from enum import Enum


class VehicleType(Enum):
    PUSHBACK = "pushback"
    TANKER = "tanker"
    CATERING = "catering"
    BAGGAGE = "baggage"



@dataclass
class GroundVehicle:
    """Represents a ground vehicle in the sim"""

    vehicle_id: str
    vehicle_type: VehicleType
    is_available: bool = True
    current_gate_id: str | None =None

    def assign_to_gate(self, gate_id: str) -> None:
        """assigns vehicle to a gate"""
        self.current_gate_id = gate_id
        self.is_available = False

    def release(self) -> None:
        """releases vehicle after completing its task"""
        self.current_gate_id = None
        self.is_available =True

        