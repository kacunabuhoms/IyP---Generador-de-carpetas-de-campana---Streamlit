import pandas as pd


def unique_clients(df: pd.DataFrame) -> list[str]:
    return sorted(df["nombre_cliente"].dropna().unique().tolist())


def campaigns_for_client(df: pd.DataFrame, nombre_cliente: str) -> pd.DataFrame:
    filtrado = df[df["nombre_cliente"] == nombre_cliente]
    deduplicado = filtrado.drop_duplicates(subset=["nombre_campana_claw"], keep="first")
    return (
        deduplicado[["cliente", "nombre_campana_claw"]]
        .sort_values("nombre_campana_claw")
        .reset_index(drop=True)
    )
