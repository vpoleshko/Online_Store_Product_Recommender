
from pathlib import Path
import pandas as pd

INPUT = Path("data/raw/events.csv")
OUTPUT = Path("data/processed")

OUTPUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

df = df.sort_values("timestamp")

split_index = int(len(df) * 0.8)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

train.to_csv(OUTPUT / "train.csv", index=False)
test.to_csv(OUTPUT / "test.csv", index=False)

print("Train:", train.shape)
print("Test:", test.shape)
print("Train transactions:", (train["event"] == "transaction").sum())
print("Test transactions:", (test["event"] == "transaction").sum())
