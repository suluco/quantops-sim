import queue
from datetime import datetime
from simulator.engine import SimulatorEngine
from simulator.state_store import StateStore
from simulator.gate_generator import generate_gates
from optimizer.engine import OptimizerEngine

def main() -> None:
    event_queue = queue.Queue()
    state_store = StateStore()
    gates = generate_gates()

    simulator = SimulatorEngine(
        event_queue=event_queue,
        sim_date=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
        state_store=state_store,
    )

    optimizer = OptimizerEngine(
        event_queue=event_queue,
        state_store=state_store,
        gates=gates,
    )

    simulator.start()
    optimizer.start()

    print("QuantOps Simulator running. Start the dashboard with:")
    print("streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()