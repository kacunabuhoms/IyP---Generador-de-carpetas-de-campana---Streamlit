from campaign_data import campaigns_for_client, unique_clients


def test_unique_clients_returns_sorted_unique_names(campanas_df):
    clientes = unique_clients(campanas_df)
    assert clientes == sorted(set(clientes))
    assert "Farmacias del ahorro" in clientes
    assert "Dairy Queen" in clientes


def test_campaigns_for_client_deduplicates_by_name(campanas_df):
    campanas = campaigns_for_client(campanas_df, "Farmacias del ahorro")
    nombres = campanas["nombre_campana_claw"].tolist()
    assert len(nombres) == len(set(nombres))


def test_campaigns_for_client_includes_known_duplicate_once(campanas_df):
    campanas = campaigns_for_client(campanas_df, "Farmacias del ahorro")
    coincidencias = campanas[campanas["nombre_campana_claw"] == "FDA JUN24 - 1"]
    assert len(coincidencias) == 1


def test_campaigns_for_client_keeps_cliente_column(campanas_df):
    campanas = campaigns_for_client(campanas_df, "Farmacias del ahorro")
    assert (campanas["cliente"] == "FDA").all()
