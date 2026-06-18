import json
from pathlib import Path

import pandas as pd
import pytest

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "Ejemplo Query.json"


@pytest.fixture
def campanas_df() -> pd.DataFrame:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        data = json.load(f)["data"]
    return pd.DataFrame(data)
