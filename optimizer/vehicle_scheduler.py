from datetime import timedelta
from models.flight import Flight
from models.ground_vehicle import GroundVehicle, VehicleType
from models.schedule import Schedule, TimeSlot


VEHICLE_DURATIONS: dict[VehicleType, int] = {
    VehicleType.PUSHBACK: 15,
    VehicleType.TANKER: 30,
    VehicleType.CATERING: 45,
    VehicleType.BAGGAGE: 40,
}


def find_available_vehicle(
    vehicle_type: VehicleType,
    flight: Flight,
    vehicles: list[GroundVehicle],
    schedule: Schedule,
) -> GroundVehicle | None:
    """
    finds first avail vehicle of a given type for a flight
    returns None if no vehicle is avail
    """
    arrival = flight.actual_arrival or flight.scheduled_arrival
    duration = VEHICLE_DURATIONS[vehicle_type]
    slot = TimeSlot(
        entity_id="",
        flight_id=flight.flight_id,
        start_time=arrival,
        end_time=arrival + timedelta(minutes=duration),
    )

    for vehicle in vehicles:
        if vehicle.vehicle_type != vehicle_type:
            continue
        existing_slots = schedule.vehicle_slots.get(vehicle.vehicle_id, [])
        conflict = any(slot.overlaps_with(s) for s in existing_slots)
        if not conflict:
            return vehicle
        
    return None


def assign_vehicles(
        flights: list[Flight],
        vehicles: list[GroundVehicle],
        schedule: Schedule,
) -> dict[str, dict[str, str | None]]:
    """
    assigns ground vehicle to all flights
    each flight gets a pushback, tanker, catering and baggage
    returns a nested dict: flight_id -> vehicle_type -> vehicle_id
    """
    assignments: dict[str, dict[str, str | None]] = {}
    sorted_flights = sorted(
        flights, key=lambda f: f.actual_arrival or f.scheduled_arrival 
    )

    for flight in sorted_flights:
        flight_assignments: dict[str, str | None] = {}
        arrival = flight.actual_arrival or flight.scheduled_arrival

        for vehicle_type in VehicleType:
            vehicle = find_available_vehicle(vehicle_type, flight, vehicles, schedule)
            if vehicle:
                duration = VEHICLE_DURATIONS[vehicle_type]
                slot = TimeSlot(
                    entity_id=vehicle.vehicle_id,
                    flight_id=flight.flight_id,
                    start_time=arrival,
                    end_time=arrival + timedelta(minutes=duration),
                )
                schedule.add_vehicle_slot(slot)
                vehicle.assign_to_gate(flight.gate_id or "unknown")
                flight_assignments[vehicle_type.value] = vehicle.vehicle_id
            else:
                flight_assignments[vehicle_type.value] = None

        assignments[flight.flight_id] = flight_assignments
    
    return assignments