import queue
import threading
from models.event import Event
from models.gate import Gate
from models.schedule import Schedule
from simulator.state_store import StateStore
from optimizer.greedy import assign_gates_greedy


class OptimizerEngine:
    
    def __init__(self, event_queue: queue.Queue, state_store: StateStore, gates: list[Gate]) -> None:
        self.event_queue = event_queue
        self.state_store = state_store
        self.gates = gates
        self.schedule = Schedule()
        self.running = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.running = True
        self._initial_assignment()
        self._thread.start()

    def _initial_assignment(self) -> None:
        flights = self.state_store.get_flights()
        if flights:
            assign_gates_greedy(flights, self.gates, self.schedule)
            for flight in flights:
                self.state_store.update_flight(flight)
    
    def _handle_event(self, event: Event) -> None:
        flights = self.state_store.get_flights()
        unassigned = [f for f in flights if f.gate_id is None]
        if unassigned:
            assign_gates_greedy(unassigned, self.gates, self.schedule)
            for flight in unassigned:
                self.state_store.update_flight(flight)
    
    def _run(self) -> None:
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self._handle_event(event)
            except queue.Empty:
                continue
