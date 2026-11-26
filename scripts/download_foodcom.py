import shutil
import sys
from pathlib import Path

import kagglehub

DATASET = "shuyangli94/food-com-recipes-and-user-interactions"
FILES = ["RAW_recipes.csv", "RAW_interactions.csv"]


def main(target):
    target.mkdir(parents=True, exist_ok=True)
    source = Path(kagglehub.dataset_download(DATASET))
    print(f"Downloaded to cache: {source}")

    for name in FILES:
        found = next(source.rglob(name), None)

        if found is None:
            sys.exit(f"{name} not found in {source}")

        shutil.copy2(found, target / name)
        print(f"  -> {target / name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/foodcom"))
