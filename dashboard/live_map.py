import plotly.graph_objects as go
from models.flight import Flight, FlightStatus
from models.ground_vehicle import GroundVehicle
from datetime import datetime


#gate positions on the schematic map
GATE_POSITIONS: dict[str, tuple[float, float]] = {}

#terminal D: 8 gates
for i, gate_num in enumerate(range(1, 9)):
    GATE_POSITIONS[f"D{gate_num:02d}"] = (i * 3.0, 8.0)

#terminal E: 5 gates
for i, gate_num in enumerate(range(1, 6)):
    GATE_POSITIONS[f"E{gate_num:02d}"] = (i * 3.0 + 3.0, 4.0)

#terminal F: 2 gates
for i, gate_num in enumerate(range(1, 3)):
    GATE_POSITIONS[f"F{gate_num:02d}"] = (i * 3.0 + 6.0, 1.0)

RUNWAY_Y = -1.5
TAXIWAY_Y = 0.5

VEHICLE_COLORS: dict[str, str] = {
    "pushback": "#f1c40f",
    "tanker": "#e74c3c",
    "catering": "#9b59b6",
    "baggage": "#1abc9c",
}

STATUS_COLORS: dict[str, str] = {
    "scheduled": "#2ecc71",
    "delayed": "#e67e22",
    "cancelled": "#e74c3c",
    "boarding": "#3498db",
    "departed": "#95a5a6",
}


def _get_flight_position(
    flight: Flight,
    sim_time: datetime,
) -> tuple[float, float] | None:
    """returns current position of a flight based on sim_time"""
    arrival = flight.actual_arrival or flight.scheduled_arrival
    departure = flight.actual_departure or flight.scheduled_departure

    if flight.status == FlightStatus.CANCELLED:
        return None

    if sim_time < arrival:
        minutes_until_arrival = (arrival - sim_time).total_seconds() / 60
        if minutes_until_arrival > 120:
            return None
        x = -3 + (120 - minutes_until_arrival) / 120 * 10
        return (x, RUNWAY_Y)

    if arrival <= sim_time <= departure:
        if flight.gate_id and flight.gate_id in GATE_POSITIONS:
            return GATE_POSITIONS[flight.gate_id]
        return None

    minutes_since_departure = (sim_time - departure).total_seconds() / 60
    if minutes_since_departure < 15:
        x = (minutes_since_departure / 15) * 10 + 15
        return (x, TAXIWAY_Y)

    return None


def build_live_map(
    flights: list[Flight],
    vehicles: list[GroundVehicle],
    sim_time: datetime,
) -> go.Figure:
    """
    builds a live schematic airport map with aircraft and ground vehicles
    draws background first, then aircraft on top
    """
    fig = go.Figure()

    #LAYER 1: runway (scatter, drawn first = bottom)
    fig.add_trace(go.Scatter(
        x=list(range(-3, 29)),
        y=[RUNWAY_Y] * 32,
        mode="lines",
        line=dict(color="#4a4a4a", width=30),
        hoverinfo="none",
        showlegend=False,
        name="_runway",
    ))

    #LAYER 2: taxiway
    fig.add_trace(go.Scatter(
        x=list(range(-3, 29)),
        y=[TAXIWAY_Y] * 32,
        mode="lines",
        line=dict(color="#3a3a3a", width=12),
        hoverinfo="none",
        showlegend=False,
        name="_taxiway",
    ))

    #LAYER 3: gates as scatter points
    gate_x = [pos[0] for pos in GATE_POSITIONS.values()]
    gate_y = [pos[1] for pos in GATE_POSITIONS.values()]
    gate_labels = list(GATE_POSITIONS.keys())

    fig.add_trace(go.Scatter(
        x=gate_x, y=gate_y,
        mode="markers+text",
        marker=dict(size=28, color="#2c3e50", symbol="square", line=dict(color="#7f8c8d", width=1)),
        text=gate_labels,
        textposition="middle center",
        textfont=dict(color="#7f8c8d", size=10),
        hoverinfo="text",
        hovertext=gate_labels,
        showlegend=False,
        name="_gates",
    ))

    #LAYER 4: terminal labels as annotations
    for terminal, x, y in [
        ("Terminal D", 10.5, 9.2),
        ("Terminal E", 9.0, 5.2),
        ("Terminal F", 7.5, 2.2),
    ]:
        fig.add_annotation(
            x=x, y=y, text=terminal,
            showarrow=False,
            font=dict(color="#bdc3c7", size=10),
        )

    fig.add_annotation(
        x=12, y=RUNWAY_Y,
        text="RUNWAY 18R/36L",
        showarrow=False,
        font=dict(color="white", size=9),
    )

    #LAYER 5: ground vehicles
    for vehicle_type, color in VEHICLE_COLORS.items():
        vx, vy, vhover = [], [], []
        for vehicle in vehicles:
            if vehicle.vehicle_type.value != vehicle_type:
                continue
            if vehicle.current_gate_id and vehicle.current_gate_id in GATE_POSITIONS:
                gx, gy = GATE_POSITIONS[vehicle.current_gate_id]
                vx.append(gx + 0.5)
                vy.append(gy - 0.8)
                vhover.append(f"{vehicle.vehicle_id}<br>{vehicle_type}<br>Gate: {vehicle.current_gate_id}")
        if vx:
            fig.add_trace(go.Scatter(
                x=vx, y=vy,
                mode="markers",
                marker=dict(size=10, color=color, symbol="circle"),
                hovertext=vhover,
                hoverinfo="text",
                name=vehicle_type,
            ))

    #LAYER 6: aircraft (top layer)
    aircraft_x, aircraft_y, aircraft_text, aircraft_color, aircraft_hover = [], [], [], [], []
    for flight in flights:
        pos = _get_flight_position(flight, sim_time)
        if pos:
            aircraft_x.append(pos[0])
            aircraft_y.append(pos[1])
            aircraft_text.append(flight.flight_id)
            aircraft_color.append(STATUS_COLORS.get(flight.status.value, "#ffffff"))
            aircraft_hover.append(
                f"{flight.flight_id}<br>{flight.airline}<br>"
                f"{flight.origin} → {flight.destination}<br>"
                f"Status: {flight.status.value}<br>"
                f"Delay: {flight.delay_minutes} min"
            )

    if aircraft_x:
        fig.add_trace(go.Scatter(
            x=aircraft_x,
            y=aircraft_y,
            mode="markers+text",
            marker=dict(
                symbol="arrow-right",
                size=20,
                color=aircraft_color,
                line=dict(color="white", width=1),
            ),
            text=aircraft_text,
            textposition="top center",
            textfont=dict(color="white", size=10),
            hovertext=aircraft_hover,
            hoverinfo="text",
            name="Aircraft",
        ))

    #layout
    fig.update_layout(
        height=550,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#1a1a2e",
        showlegend=True,
        xaxis=dict(visible=False, range=[-4, 30]),
        yaxis=dict(visible=False, range=[-3, 10]),
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"Live airport map — {sim_time.strftime('%H:%M') if sim_time else ''}",
        legend=dict(bgcolor="rgba(0,0,0,0.5)", font=dict(color="white")),
    )

    return fig