import time
import json
import numpy as np
from datetime import datetime
from models.schedule import Schedule
from simulator.flight_generator import generate_flights
from simulator.delay_model import apply_delay
from simulator.gate_generator import generate_gates
from optimizer.greedy import assign_gates_greedy
from optimizer.lp_optimizer import assign_gates_lp
from optimizer.simulated_annealing import assign_gates_sa
from optimizer.astar import assign_gates_astar


def _gate_distribution_score(assignmens: dict[str, str | None]) -> float:
    """
    measures how evenly flights are distributes across gates
    lower = more balanced, 0 = perfect balance
    """
    gate_counts: dict[str, int] = {}
    for gate_id in assignmens.values():
        if gate_id:
            gate_counts[gate_id] = gate_counts.get(gate_id, 0) + 1
    if not gate_counts:
        return 0.0
    counts = list(gate_counts.values())
    return float(np.std(counts))


def _count_remaining_conflict(assignments: dict, flights: list, gates: list) -> int:
    """builds a schedule from assignments and counts conflicts"""
    from models.schedule import TimeSlot
    schedule = Schedule()
    flight_map = {f.flight_id: f for f in flights}
    for flight_id, gate_id in assignments.items():
        if gate_id:
            flight = flight_map[flight_id]
            slot = TimeSlot(
                entity_id=gate_id,
                flight_id=flight_id,
                start_time=flight.actual_arrival or flight.scheduled_arrival,
                end_time=flight.actual_departure or flight.scheduled_departure,
            )
            schedule.add_gate_slot(slot)
    return len(schedule.get_conflicts())


def run_benchmark(n_flights: int = 20, n_runs: int = 5) -> dict:
    """
    uns all four algorithms on the same dataset and measures performance
    returns a dict with results per algorithm
    """
    results = {
        "greedy": {"times": [], "conflicts": [], "distribution": []},
        "lp": {"times": [], "conflicts": [], "distribution": []},
        "sa": {"times": [], "conflicts": [], "distribution": []},
        "astar": {"times": [], "conflicts": [], "distribution": []},
    }

    rng = np.random.default_rng(seed=42)

    for run in range(n_runs):
        date = datetime(2026, 3, 13)
        flights = generate_flights(date, n=n_flights)
        for flight in flights:
            apply_delay(flight, rng)
        gates = generate_gates()

        algorithms = {
            "greedy": assign_gates_greedy,
            "lp": assign_gates_lp,
            "sa": assign_gates_sa,
            "astar": assign_gates_astar,
        }

        for name, algo in algorithms.items():
            #reset flight gate assignments
            for flight in flights:
                flight.gate_id = None
            
            schedule = Schedule()
            start = time.perf_counter()
            assignments = algo(flights, gates, schedule)
            elapsed = time.perf_counter() - start

            conflicts = _count_remaining_conflict(assignments, flights, gates)
            distribution = _gate_distribution_score(assignments)

            results[name]["times"].append(round(elapsed, 4))
            results[name]["conflicts"].append(conflicts)
            results[name]["distribution"].append(round(distribution, 3))

        print(f"[Benchmark] Run {run + 1}/{n_runs} complete")
    

    summary = {}
    for name, data in results.items():
        summary[name] = {
            "avg_time_ms": round(np.mean(data["times"]) * 1000, 2),
            "avg_conflicts": round(np.mean(data["conflicts"]), 2),
            "avg_distribution": round(np.mean(data["distribution"]), 3),
        }
    
    return summary


def save_benchmark(results: dict, path: str = "models/benchmark_results.json") -> None:
    """saves benchmark results to disk"""
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
        print(f"[Benchmark] Results saved to {path}")


if __name__ == "__main__":
    print("[Benchmark] Starting benchmark...")
    results = run_benchmark(n_flights=20, n_runs=5)
    save_benchmark(results)
    print("\n=== RESULTS ===")
    for algo, metrics in results.items():
        print(f"{algo:8} | {metrics['avg_time_ms']:8.2f}ms | {metrics['avg_conflicts']} conflicts | distribution std: {metrics['avg_distribution']}")