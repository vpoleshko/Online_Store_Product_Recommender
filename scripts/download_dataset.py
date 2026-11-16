import shutil
import sys
from pathlib import Path

import kagglehub

DATASET = "psparks/instacart-market-basket-analysis"
FILES = [
    "departments.csv",
    "aisles.csv",
    "products.csv",
    "orders.csv",
    "order_products__prior.csv",
    "order_products__train.csv",
]


def main(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    src = Path(kagglehub.dataset_download(DATASET))
    print(f"Downloaded to cache: {src}")

    for name in FILES:
        found = next(src.rglob(name), None)
        if found is None:
            sys.exit(f"{name} not found in {src}")
        shutil.copy2(found, target / name)
        print(f"  -> {target / name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw"))
