import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class WeatherType(Enum):
    CLEAR = "clear"
    WIND = "wind"
    FOG = "fog"
    STORM = "storm"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"


@dataclass
class WeatherEvent:
    """represents weahter event during the simulation"""
    weather_type: WeatherType
    start_time: datetime
    end_time: datetime
    delay_factor: float

    def is_active(self, sim_time: datetime) -> bool:
        """returns True if weather event is active at sim_time"""
        return self.start_time <= sim_time <= self.end_time
    

def generate_weather_events(date: datetime, rng: np.random.Generator) -> list[WeatherEvent]:
    events = []
    n_events = int(rng.integers(0, 4))

    for _ in range(n_events):
        hour = int(rng.integers(6, 21))
        duration = int(rng.integers(30, 180))
        start = date.replace(hour=hour, minute=0, second=0)
        end = start + timedelta(minutes=duration)

        roll = rng.random()
        if roll < 0.4:
            weather_type = WeatherType.WIND
            delay_factor = 1.5
        elif roll < 0.65:
            weather_type = WeatherType.FOG
            delay_factor = 2.0
        elif roll < 0.8:
            weather_type = WeatherType.STORM
            delay_factor = 3.5
        elif roll < 0.92:
            weather_type = WeatherType.SNOW
            delay_factor = 4.0
        else:
            weather_type = WeatherType.THUNDERSTORM
            delay_factor = 4.5
        
        events.append(WeatherEvent(
            weather_type=weather_type,
            start_time=start,
            end_time=end,
            delay_factor=delay_factor,
        ))
    
    return events


def get_active_weather(
        events: list[WeatherEvent],
        sim_time: datetime,
) -> WeatherEvent | None:
    """returns the most severe active weather event at sim_time, or None"""
    active = [e for e in events if e.is_active(sim_time)]
    if not active:
        return None
    return max(active, key=lambda e: e.delay_factor)
