# QuantOps Simulator

An event-driven airport operations optimizer built in Python. The simulator generates realistic flight schedules, detects gate conflicts automatically, and replans in real-time using four optimization algorithms. A live Streamlit dashboard visualizes the current airport status, including a schematic live map with moving aircraft and ground vehicles.

Built by Joren Veldhuis, student Industrial Engineering & Management at Hanze University of Applied Sciences, as a personal project in preparation for an internship at Airbus or CERN.

---

## What it does

The system simulates a full day of operations at Amsterdam Airport Schiphol on an accelerated time axis (1 simulated day = 30 seconds real time). It generates flights, applies realistic delays using Monte Carlo simulation, detects gate conflicts, and automatically replans using the most appropriate algorithm based on conflict severity. Weather events such as storms and snow trigger cascade delays across connected flights.

---

## Architecture

The system consists of three layers running in parallel threads:

**Simulator** — Generates flights and events on an accelerated time axis. Uses a Poisson distribution for delays and models peak hours (07:00–09:00 and 17:00–19:00) and off-peak hours. Pushes events to a shared queue.

**Optimizer** — Listens to the event queue and assigns gates to flights. Automatically selects the best algorithm based on conflict severity:
- 1–3 conflicts → Greedy
- 4–10 conflicts → Linear Programming (PuLP)
- 11+ conflicts → Simulated Annealing
- Cascade (>40% flights affected) → A*

**Dashboard** — Streamlit webapp that reads from a shared state store and rerenders every 3 seconds. Contains six tabs: Flights, Event log, Gantt chart, Scenario injection, Algorithm comparison, and Live airport map.

---

## Installation

**Requirements:** Python 3.11+, Node.js (for npm), Git

```bash
# Clone the repository
git clone https://github.com/jorenveldhuis/quantops-simulator.git
cd quantops-simulator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the simulator

```bash
streamlit run dashboard/app.py
```

The simulator and optimizer start automatically in the background. Open the browser at `http://localhost:8501`.

---

## Training the ML model

The delay prediction model must be trained before first use:

```bash
python -m optimizer.train
```

This generates 10,000 training samples (200 simulated days) and trains a Random Forest classifier. The model is saved to `models/delay_model.pkl`. Expected accuracy: ~74%.

---

## Running the algorithm benchmark

```bash
python -m optimizer.benchmark
```

Runs all four algorithms on the same dataset and saves results to `models/benchmark_results.json`. Results are automatically displayed in the Comparison tab of the dashboard.

---

## Project structure

```
quantops-simulator/
├── dashboard/
│   ├── app.py                  # Main Streamlit dashboard
│   └── live_map.py             # Live airport map visualization
├── models/
│   ├── flight.py               # Flight dataclass
│   ├── gate.py                 # Gate dataclass
│   ├── ground_vehicle.py       # Ground vehicle dataclass
│   ├── event.py                # Event dataclass
│   └── schedule.py             # Schedule and TimeSlot dataclasses
├── optimizer/
│   ├── engine.py               # Optimizer engine (thread)
│   ├── greedy.py               # Greedy gate assignment
│   ├── lp_optimizer.py         # Linear Programming optimizer (PuLP)
│   ├── simulated_annealing.py  # Simulated Annealing optimizer
│   ├── astar.py                # A* optimizer
│   ├── conflict_detector.py    # Conflict detection and severity classification
│   ├── cascade_detector.py     # Cascade failure detection
│   ├── vehicle_scheduler.py    # Ground vehicle scheduling
│   ├── ml_model.py             # ML delay prediction (Random Forest)
│   ├── train.py                # ML training script
│   └── benchmark.py            # Algorithm benchmark
├── simulator/
│   ├── engine.py               # Simulator engine (thread)
│   ├── flight_generator.py     # Flight generation with peak/off-peak patterns
│   ├── delay_model.py          # Monte Carlo delay simulation
│   ├── event_generator.py      # Event creation
│   ├── state_store.py          # Thread-safe shared state
│   ├── statistics.py           # Flight statistics
│   ├── weather.py              # Weather event generation
│   ├── gate_generator.py       # Gate generation (15 gates, 3 terminals)
│   └── vehicle_generator.py    # Ground vehicle generation
├── tests/
│   └── test_models.py          # Unit tests (19 tests)
├── main.py                     # Entry point (without dashboard)
└── requirements.txt
```

---

## Technology stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Dashboard | Streamlit + Plotly |
| LP optimizer | PuLP (CBC solver) |
| ML module | scikit-learn (Random Forest) |
| Threading | stdlib: threading, queue |
| Data | pandas, numpy |
| Tests | pytest |
| Version control | Git + GitHub |

---

## Dashboard tabs

**Flights** — Live table of all flights with gate assignment, delay, and status. Includes CSV export.

**Event log** — Real-time feed of all simulator events, color-coded by severity (green/orange/red).

**Gantt chart** — Gate planning visualized as a timeline. Color-coded by flight status. Updates every 3 seconds.

**Scenario** — Manually inject delays, cancellations, or maintenance events. The optimizer automatically replans after injection.

**Comparison** — Algorithm benchmark results visualized as bar charts. Shows execution time, remaining conflicts, and gate distribution quality.

**Live map** — Schematic airport map showing aircraft positions (approaching, at gate, departing) and ground vehicle locations in real time.

---

## ML model

The delay prediction model uses a Random Forest classifier trained on 10,000 simulated flights. Features include hour of arrival, day of week, airline, destination, turnaround time, gate occupancy, passenger count, and active weather conditions. Achieved 74.25% cross-validation accuracy.

The model is integrated into the optimizer and used proactively when assigning gates — flights with a high predicted delay probability are prioritized for gates with more buffer time.

---

## Algorithm comparison

| Algorithm | Avg time | Conflicts | Gate distribution |
|---|---|---|---|
| Greedy | 0.02ms | 0 | 2.36 std |
| LP | 371ms | 0 | 0.64 std |
| Simulated Annealing | 0.80ms | 0 | 0.54 std |
| A* | 763ms | 0 | 2.36 std |

Simulated Annealing achieves near-optimal gate distribution at a fraction of LP's computation time, making it the preferred algorithm for medium-to-large conflict scenarios.

---

## Running tests

```bash
pytest tests/test_models.py -v
```

19 tests covering all core components. Expected runtime: ~18 seconds.
