import queue
import threading
from models.event import Event
from models.gate import Gate
from models.schedule import Schedule
from simulator.state_store import StateStore
from optimizer.greedy import assign_gates_greedy
from optimizer.lp_optimizer import assign_gates_lp
from optimizer.conflict_detector import count_conflicts, classify_conflict_severity, get_conflicting_flights


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

    def stop(self) -> None:
        self.running = False

    def _initial_assignment(self) -> None:
        flights = self.state_store.get_flights()
        if flights:
            assign_gates_greedy(flights, self.gates, self.schedule)
            for flight in flights:
                self.state_store.update_flight(flight)
    
    def _replan(self) -> None:
        """
        detects conflicts and chooses appropriate algorithm:
        small: greedy
        large: LP
        cascade: full replan with LP
        """
        flights = self.state_store.get_flights()
        total = len(flights)
        conflict_count = count_conflicts(flights, self.schedule)
        severity = classify_conflict_severity(conflict_count, total)

        if severity == "none":
            return
        
        conflicting = get_conflicting_flights(flights, self.schedule)

        if severity == "small":
            assign_gates_greedy(conflicting, self.gates, self.schedule)
            algo = "greedy"
        elif severity == "large":
            assign_gates_lp(conflicting, self.gates, self.schedule)
            algo = "LP"
        else:   #cascade
            assign_gates_lp(flights, self.gates, self.schedule)
            algo ="LP (full replan)"
        
        for flights in flights:
            self.state_store.update_flight(flights)
        
        print(f"[Optimizer] {severity.upper()} - {conflict_count} conflicts resolved with {algo}")

    def _handle_event(self, event: Event) -> None:
        flights = self.state_store.get_flights()
        unassigned = [f for f in flights if f.gate_id is None]
        if unassigned:
            assign_gates_greedy(unassigned, self.gates, self.schedule)
            for flight in unassigned:
                self.state_store.update_flight(flight)
        self._replan()
    
    def _run(self) -> None:
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self._handle_event(event)
            except queue.Empty:
                continue
    
    def force_replan(self) -> None:
        """
        clears schedule and replans all flights from scratch
        excludes cancelled flights that haven't arived yet
        """
        from datetime import datetime
        from models.flight import FlightStatus
        
        self.schedule = Schedule()
        flights = self.state_store.get_flights()
        sim_time = self.state_store.get_sim_time() or datetime.now()

        active_flights = [
            f for f in flights
            if not (
                f.status == FlightStatus.CANCELLED and
                (f.actual_arrival or f.scheduled_arrival) > sim_time
            )
        ]

        if active_flights:
            assign_gates_greedy(active_flights, self.gates, self.schedule)
            for flight in active_flights:
                self.state_store.update_flight(flight)