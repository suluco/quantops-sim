from collections import defaultdict
from models.flight import Flight


def flights_per_hour(flights: list[Flight]) -> dict[int, int]:
    """returns the number of arriving flights per hour of the day"""
    counts: dict[int, int] = defaultdict(int)
    for flight in flights:
        hour = flight.scheduled_arrival.hour
        counts[hour] += 1
    return dict(sorted(counts.items()))


def average_turnaround(flights: list[Flight]) -> float:
    """returns avg turnaround time in min across all flights"""
    if not flights:
        return 0.0
    return sum(f.turnaround_minutes() for f in flights) / len(flights)


def peak_hour_ratio(flights: list[Flight]) -> float:
    """returns ratio of flights during peak hrs vs tot."""
    peak_hours = set(range(7, 9)) | set(range(17, 19))
    peak = sum(1 for f in flights if f.scheduled_arrival.hour in peak_hours)
    return peak / len(flights) if flights else 0.0

def print_summary(flights: list[Flight]) -> None:
    """prints summary of flight stats to the console"""
    print(f"Total flights: {len(flights)}")
    print(f"Average turnaround: {average_turnaround(flights):.1f} min")
    print(f"Peak hour ratio: {peak_hour_ratio(flights):.1%}")
    print("\nFlights per hour:")
    for hour, count in flights_per_hour(flights).items():
        bar = "█" * count
        print(f"  {hour:02d}:00 - {bar} ({count})")
