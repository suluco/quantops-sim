from models.flight import Flight
from models.schedule import Schedule, TimeSlot
from datetime import timedelta


BUFFER_MINUTES = 15


def detect_conflicts(flights: list[Flight], schedule: Schedule) -> list[tuple[TimeSlot, TimeSlot]]:
    """
    detects all gate conflicts in current schedule
    returns list of conflicting TimeSlot pairs
    """
    return schedule.get_conflicts()

def count_conflicts(flights: list[Flight], schedule: Schedule) -> int:
    return len(detect_conflicts(flights, schedule))

def classify_conflict_severity(conflict_count: int, total_flights: int) -> str:
    """
    classifies severity of conflicts based on count and ratio
    'none': no conflicts
    'small': 1-3 conflicts (uses greedy)
    'large': 4+ conflicts (uses LP)
    'cascade': >=40% of flights in conflict, results in full replan
    """
    if conflict_count == 0:
        return "none"
    ratio = conflict_count / total_flights if total_flights > 0 else 0
    if ratio > 0.4:
        return "cascade"
    if conflict_count <= 3:
        return "small"
    return "large"

def get_conflicting_flights(
        flights: list[Flight], schedule: Schedule
) -> list[Flight]:
    conflicts = detect_conflicts(flights, schedule)
    conflicting_ids = set()
    for slot_a, slot_b in conflicts:
        conflicting_ids.add(slot_a.flight_id)
        conflicting_ids.add(slot_b.flight_id)
    return [f for f in flights if f.flight_id in conflicting_ids]


    
