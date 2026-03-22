from models.ground_vehicle import GroundVehicle, VehicleType

def generate_vehicles() -> list[GroundVehicle]:
    """generates realistic set of ground vehicles for AMS"""
    vehicles = []

    for i in range(1, 7):
        vehicles.append(GroundVehicle(
            vehicle_id=f"PB{i:02d}",
            vehicle_type=VehicleType.PUSHBACK,
        ))

    for i in range(1, 9):
        vehicles.append(GroundVehicle(
            vehicle_id=f"TK{i:02}",
            vehicle_type=VehicleType.TANKER
        ))
    
    for i in range(1, 6):
        vehicles.append(GroundVehicle(
            vehicle_id=f"CT{i:02d}",
            vehicle_type=VehicleType.CATERING,
        ))

    for i in range(1, 9):
        vehicles.append(GroundVehicle(
            vehicle_id=f"BG{i:02d}",
            vehicle_type=VehicleType.BAGGAGE,
        ))

    return vehicles
