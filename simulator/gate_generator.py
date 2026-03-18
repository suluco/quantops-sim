from models.gate import Gate, GateType


def generate_gates() -> list[Gate]:
    """
    generates realistic set of 25 gates for AMS divided across
    3 terminals with different gate types
    """
    gates = []

    for i in range(1, 16):
        gates.append(Gate(
            gate_id=f"D{i:02d}",
            terminal="D",
            gate_type=GateType.SCHENGEN,
            capacity=180,
        ))

    for i in range(1, 8):
        gates.append(Gate(
            gate_id=f"E{i:02d}",
            terminal="E",
            gate_type=GateType.NON_SCHENGEN,
            capacity=220,
        ))

    for i in range(1, 4):
        gates.append(Gate(
            gate_id=f"F{i:02d}",
            terminal="F",
            gate_type=GateType.NON_SCHENGEN,
            capacity=350,
        ))

    return gates