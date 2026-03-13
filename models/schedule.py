from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TimeSlot:
    """Represents a timeslot for a gate or vehicle assignment"""

    entity_id: str
    flight_id: str
    start_time: datetime
    end_time: datetime

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """returns True if this slot overlaps with another slot"""
        return self.start_time < other.end_time and self.end_time > other.start_time


@dataclass
class Schedule:
    """holds the full planning of time slots per gate and vehicle"""

    gate_slots: dict[str, list[TimeSlot]] = field(default_factory=dict)
    vehicle_slots: dict[str, list[TimeSlot]] = field(default_factory=dict)

    def add_gate_slot(self, slot: TimeSlot) -> None:
        """adds a time slot to a gate's schedule"""
        if slot.entity_id not in self.gate_slots:
            self.gate_slots[slot.entity_id] = []
        self.gate_slots[slot.entity_id].append(slot)
    
    def get_conflicts(self) -> list[tuple[TimeSlot, TimeSlot]]:
        """returns all overlapping timeslots over all gates"""
        conflicts = []
        for slots in self.gate_slots.values():
            for i, slot_a in enumerate(slots):
                for slot_b in slots[i + 1:]:
                    if slot_a.overlaps_with(slot_b):
                        conflicts.append((slot_a, slot_b))
        return conflicts
    
    