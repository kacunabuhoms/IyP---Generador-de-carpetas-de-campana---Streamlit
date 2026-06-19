import pandas as pd
import requests

import config


def get_campaigns() -> pd.DataFrame:
    response = requests.get(
        config.get_campaigns_api_url(),
        headers={"Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError("La API de campañas respondió ok=false")
    return pd.DataFrame(data["campanas"])
