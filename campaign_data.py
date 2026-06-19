import pandas as pd


def unique_clients(df: pd.DataFrame) -> list[str]:
    return sorted(df["cliente"].dropna().unique().tolist())


def campaigns_for_client(df: pd.DataFrame, cliente: str) -> pd.DataFrame:
    filtrado = df[df["cliente"] == cliente]
    deduplicado = filtrado.drop_duplicates(subset=["campana"], keep="first")
    return (
        deduplicado[["cliente", "campana"]]
        .sort_values("campana")
        .reset_index(drop=True)
    )
