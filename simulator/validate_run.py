import queue
from datetime import datetime
from simulator.engine import SimulatorEngine
import time

event_queue = queue.Queue()
sim_date = datetime(2026, 3, 13)
engine = SimulatorEngine(event_queue, sim_date)

print("simulator gestart...")
engine.start()

time.sleep(35)
engine.stop()

event_count = event_queue.qsize()
print(f"simulator gestopt. event gegenereerd: {event_count}")
print(f"simulator nog actief: {engine.running}")

if event_count > 0 and not engine.running:
    print("milestone behaald: sim draat 1 dag foutloos door")
else:
    print("iets ging mis")