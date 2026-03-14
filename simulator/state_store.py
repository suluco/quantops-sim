import threading
from datetime import datetime
from models.flight import Flight
from models.event import Event
from models.schedule import Schedule


class StateStore:
    """
    Thread-safe shared state between simulator, optimizer and dashboard.
    All reads and writes are protected by a threading lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.flights: dict[str, Flight] = {}
        self.events: list[Event] = []
        self.schedule: Schedule = Schedule()
        self.sim_time: datetime | None = None
        self.is_running: bool = False

    def update_flight(self, flight: Flight) -> None:
        """Adds or updates a flight in the state store."""
        with self._lock:
            self.flights[flight.flight_id] = flight

    def add_event(self, event: Event) -> None:
        """Appends an event to the event log."""
        with self._lock:
            self.events.append(event)

    def get_flights(self) -> list[Flight]:
        """Returns a snapshot of all flights."""
        with self._lock:
            return list(self.flights.values())

    def get_events(self, limit: int = 50) -> list[Event]:
        """Returns the most recent events up to limit."""
        with self._lock:
            return self.events[-limit:]

    def update_sim_time(self, sim_time: datetime) -> None:
        """Updates the current simulated time."""
        with self._lock:
            self.sim_time = sim_time

    def get_sim_time(self) -> datetime | None:
        """Returns the current simulated time."""
        with self._lock:
            return self.sim_time

    def set_running(self, running: bool) -> None:
        """Sets the simulator running state."""
        with self._lock:
            self.is_running = running

    def get_summary(self) -> dict:
        """Returns a summary of current KPIs."""
        with self._lock:
            flights = list(self.flights.values())
            total = len(flights)
            delayed = sum(1 for f in flights if f.is_delayed())
            cancelled = sum(1 for f in flights if f.status.value == "cancelled")
            on_time = total - delayed - cancelled
            return {
                "total": total,
                "on_time": on_time,
                "delayed": delayed,
                "cancelled": cancelled,
                "on_time_pct": round(on_time / total * 100, 1) if total > 0 else 0.0,
            }