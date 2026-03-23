import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
import joblib
from datetime import datetime
from models.flight import Flight
from simulator.weather import WeatherEvent


airline_encoder = LabelEncoder()
destination_encoder = LabelEncoder()


def extract_features(
        flight: Flight,
        occupancy_per_hour: dict[int, int],
        active_weather: WeatherEvent | None = None,
) -> dict:
    """extracts features from flight for ML prediction"""
    arrival = flight.actual_arrival or flight.scheduled_arrival
    return{
        "hour": arrival.hour,
        "weekday": arrival.weekday(),
        "airline": flight.airline,
        "destination": flight.destination,
        "turnaround": flight.turnaround_minutes(),
        "occupancy": occupancy_per_hour.get(arrival.hour, 0),
        "has_weather": 1 if active_weather else 0,
        "weather_factor": active_weather.delay_factor if active_weather else 1.0,
        "passenger_count": flight.passenger_count,
    }


def build_training_data(n_days: int = 200) -> pd.DataFrame:
    """
    generates training data by simulating n days of flights
    returns a dataframe with features and target label
    """
    from simulator.flight_generator import generate_flights
    from simulator.delay_model import apply_delay
    from simulator.statistics import flights_per_hour
    from simulator.weather import generate_weather_events, get_active_weather

    rng = np.random.default_rng(seed=0)
    rows = []

    for day in range(n_days):
        date = datetime(2026, 1, 1) + pd.Timedelta(days=day)
        flights = generate_flights(date, n=50)
        weather_events = generate_weather_events(date, rng)

        for flight in flights:
            apply_delay(flight, rng)

        occupancy = flights_per_hour(flights)

        for flight in flights:
            arrival = flight.actual_arrival or flight.scheduled_arrival
            active_weather = get_active_weather(weather_events, arrival)
            features = extract_features(flight, occupancy, active_weather)
            features["delayed"] = 1 if flight.is_delayed() else 0
            rows.append(features)

    return pd.DataFrame(rows)

def train_model(df: pd.DataFrame) -> RandomForestClassifier:
    """
    trains random forest classifier on provided dataframe
    returns the trained model
    """
    df = df.copy()
    df["airline"] = airline_encoder.fit_transform(df["airline"])
    df["destination"] = destination_encoder.fit_transform(df["destination"])

    X = df.drop(columns=["delayed"])
    Y = df["delayed"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(model, X, Y, cv=5, scoring="accuracy")
    print(f"[ML] Cross-validation accuracy: {scores.mean():.2%} ± {scores.std():.2%}")

    model.fit(X, Y)
    return model


def save_model(model: RandomForestClassifier, path: str = "models/delay_model.pkl") -> None:
    """saves trained model to the disk"""
    joblib.dump({
        "model": model,
        "airline_encoder": airline_encoder,
        "destination_encoder": destination_encoder,
    }, path)
    print(f"[ML] Model saved to {path}")


def load_model(path: str = "models/delay_model.pkl") -> RandomForestClassifier:
    """loades trained model from disk"""
    data = joblib.load(path)
    airline_encoder.classes_ = data["airline_encoder"].classes_
    destination_encoder.classes = data["destination_encoder"].classes_
    return data["model"]


def predict_delay(
    flight: Flight,
    model: RandomForestClassifier,
    occupancy_per_hour: dict[int, int],
    active_weather: WeatherEvent | None = None,
) -> float:
    """
    predicts probability of delay for a flight
    returns a float between 0 and 1
    """
    features = extract_features(flight, occupancy_per_hour, active_weather)
    df = pd.DataFrame([features])
    df["airline"] = airline_encoder.transform(df["airline"])
    df["destination"] = destination_encoder.transform(df["destination"])
    prob = model.predict_proba(df)[0][1]
    return float(prob)