from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventType(Enum):
    DELAY = "delay"
    CANCEL = "cancel"
    MAINTENANCE = "maintenance"
    GATE_CHANGE = "gate_change"


class EventSeverity(Enum):
    SMALL = "small"
    LARGE = "large"
    CRITICAL = "critical"


@dataclass
class Event:
    """represents an operational event in the simulation"""

    event_id: str
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime
    entity_id: str
    description: str
    resolved: bool = False

    def resolve(self) -> None:
        """marks the event as resolved"""
        self.resolved = True