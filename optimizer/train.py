from optimizer.ml_model import build_training_data, train_model, save_model


def main() -> None:
    """generates training data, trains the model and saves it to disk"""
    print("[ML] Generating training data (200 days)...")
    df = build_training_data(n_days=200)
    print(f"[ML] Training data: {len(df)} samples, {df['delayed'].mean():.1%} delayed")

    print("[ML] Training Random Forest...")
    model = train_model(df)

    save_model(model)
    print("[ML] Done.")


if __name__ == "__main__":
    main()