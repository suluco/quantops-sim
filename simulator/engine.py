import threading
import queue
import time
from datetime import datetime, timedelta
import numpy as np

from models.flight import Flight
from models.event import Event
from simulator.flight_generator import generate_flights
from simulator.delay_model import apply_delay
from simulator.event_generator import create_delay_event, create_cancel_event
from simulator.weather import generate_weather_events, get_active_weather, WeatherEvent


SIMULATION_SPEED = 60 * 24 / 30


class SimulatorEngine:
    """
  core sim engine. runs in seperate thread and pushes
  events to shared queue as simulated time progresses
    """

    def __init__(self, event_queue: queue.Queue, sim_date: datetime, state_store=None) -> None:
        self.event_queue = event_queue
        self.sim_date = sim_date
        self.state_store = state_store
        self.running = False
        self.sim_time = sim_date.replace(hour=0, minute=0, second=0)
        self.flights: list[Flight] = []
        self.rng = np.random.default_rng()
        self.weather_events: list[WeatherEvent] = []
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        """starts the sim in background thread"""
        self.running = True
        self.flights = generate_flights(self.sim_date)
        self.weather_events = generate_weather_events(self.sim_date, self.rng)
        for flight in self.flights:
            apply_delay(flight, self.rng)
            if self.state_store:
                self.state_store.update_flight(flight)
        if self.flights:
            first = min(self.flights, key=lambda f: f.actual_arrival or f.scheduled_arrival)
            self.sim_time = (first.actual_arrival or first.scheduled_arrival).replace(second=0, microsecond=0)
        self._thread.start()
    
    def stop(self) -> None:
        self.running = False

    def _advance_time(self) -> None:
        self.sim_time += timedelta(minutes=1)

    def _check_flights(self) -> None:
        """Checks all flights and pushes events for those arriving at current sim time."""
        import uuid
        from models.event import Event, EventType, EventSeverity

        active_weather = get_active_weather(self.weather_events, self.sim_time)

        for flight in self.flights:
            arrival = flight.actual_arrival or flight.scheduled_arrival
            if (arrival.hour == self.sim_time.hour
                    and arrival.minute == self.sim_time.minute
                    and arrival.date() == self.sim_time.date()):

                if active_weather and flight.is_delayed():
                    extra_delay = int(flight.delay_minutes * (active_weather.delay_factor - 1))
                    flight.delay_minutes += extra_delay
                    from datetime import timedelta
                    flight.actual_arrival += timedelta(minutes=extra_delay)
                    flight.actual_departure += timedelta(minutes=extra_delay)
                    if self.state_store:
                        self.state_store.update_flight(flight)

                if flight.is_delayed():
                    event = create_delay_event(flight, self.sim_time)
                else:
                    event = Event(
                        event_id=str(uuid.uuid4()),
                        event_type=EventType.GATE_CHANGE,
                        severity=EventSeverity.SMALL,
                        timestamp=self.sim_time,
                        entity_id=flight.flight_id,
                        description=f"Flight {flight.flight_id} arriving on schedule",
                    )
                
                if active_weather:
                    event.description += f" [{active_weather.weather_type.value.upper()}]"

                self.event_queue.put(event)
                if self.state_store:
                    self.state_store.add_event(event)

    def _run(self) -> None:
        """Main simulation loop. Advances time and generates events."""
        if self.state_store:
            self.state_store.set_running(True)
        end_time = self.sim_date.replace(hour=23, minute=0, second=0)
        while self.running and self.sim_time.date() == self.sim_date.date():
            self._check_flights()
            self._advance_time()
            if self.state_store:
                self.state_store.update_sim_time(self.sim_time)
            time.sleep(60 / SIMULATION_SPEED)
        self.running = False
        if self.state_store:
            self.state_store.set_running(False)

